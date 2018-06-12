from nx import *

__all__ = ["api_jobs"]

def api_jobs(**kwargs):
    if not kwargs.get("user", None):
        return {'response' : 401, 'message' : 'unauthorized'}

    db = kwargs.get("db", DB())

    if "restart" in kwargs:
        jobs = [int(i) for i in kwargs["restart"]]
        db.query("""
            UPDATE jobs SET
                status=5,
                retries=0,
                creation_time=%s,
                start_time=NULL,
                end_time=NULL,
                message='Restart requested'
            WHERE
                id IN %s
            RETURNING id
            """,
            [time.time(), tuple(jobs)]
            )
        result = [r[0] for r in db.fetchall()]
        db.commit()
        logging.info("Restarted jobs {}".format(result))
        #TODO: smarter message
        return {"response" : 200, "data" : result, "message" : "Jobs restarted"}

    if "abort" in kwargs:
        jobs = [int(i) for i in kwargs["abort"]]
        db.query("""
            UPDATE jobs SET
                status=4,
                end_time=%s,
                message='Aborted'
            WHERE
                id IN %s
            RETURNING id
            """,
            [time.time(), tuple(jobs)]
            )
        result = [r[0] for r in db.fetchall()]
        logging.info("Aborted jobs {}".format(result))
        db.commit()
        #TODO: smarter message
        return {"response" : 200, "data" : result, "message" : "Jobs abort"}

    view = kwargs.get("view", "all")

    data = []
    db.query("""SELECT
                id,
                id_asset,
                id_action,
                id_service,
                id_user,
                priority,
                retries,
                status,
                progress,
                message,
                creation_time,
                start_time,
                end_time
            FROM jobs LIMIT 100
            """)
    for id, id_asset, id_action, id_service, id_user, priority, retries, status, progress, message, ctime, stime, etime in db.fetchall():
        row = {
                "id" : id,
                "id_asset" : id_asset,
                "id_action" : id_action,
                "id_service" : id_service,
                "id_user" : id_user,
                "priority" : priority,
                "retries" : retries,
                "status" : status,
                "progress" : progress,
                "message" : message,
                "ctime" : ctime,
                "stime" : stime,
                "etime" : etime
            }
        data.append(row)

    return {"response" : 200, "data" : data}
