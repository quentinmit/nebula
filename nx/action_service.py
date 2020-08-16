from nebula import *
from nx.jobs import Action, get_job

__all__ = ["ActionService"]

class ActionService(BaseService):
    def on_init(self):
        self.actions = []
        db = DB()
        db.query("SELECT id, title, service_type, settings FROM actions ORDER BY id")
        for id_action, title, service_type, settings in db.fetchall():
            if service_type == self.service_type:
                logging.debug("Registering action {}".format(title))
                self.actions.append(Action(id_action, title, xml(settings)))
        self.reset_jobs()

    def reset_jobs(self):
        db = DB()
        db.query("""
            UPDATE jobs SET
                id_service=NULL,
                progress=0,
                retries=0,
                status=5,
                message='Restarting after service restart',
                start_time=0,
                end_time=0
            WHERE
                id_service=%s AND STATUS IN (0,1,5)
            RETURNING id
            """,
                [self.id_service]
            )
        for id_job, in db.fetchall():
            logging.info("Restarting job ID {} ({} restarted)".format(id_job, self.service_type))
        db.commit()


    def job_fail(self, job, message="Processing failed", critical=False):
        job.fail(message=message)


    def on_main(self):
        db = DB()
        job = get_job(
                self.id_service,
                [action.id for action in self.actions],
                db=db
            )
        if not job:
            return
        logging.info("Got {}".format(job))

        try:
            self.process_job(job)
        except Exception as e:
            self.job_fail(job, message="Job failed: %s" % (e,))
