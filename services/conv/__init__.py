from nebula import *
from nx.jobs import Action, get_job
from nx.action_service import ActionService

from services.conv.encoders import *

FORCE_INFO_EVERY = 20

available_encoders = {
        "ffmpeg" : NebulaFFMPEG
    }

class Service(ActionService):
    service_type = "conv"

    def process_job(self, job):
        asset = job.asset
        action = job.action

        try:
            job_params = job.settings
        except Exception:
            log_traceback()
            job_params = {}

        tasks = action.settings.findall("task")
        job_start_time = last_info_time = time.time()

        for id_task, task in enumerate(tasks):
            task_start_time = time.time()

            try:
                using = task.attrib["mode"]
                if not using in available_encoders:
                    continue
            except KeyError:
                self.job_fail(job, "Wrong encoder type specified for task {}".format(id_task), critical=True)
                return

            logging.debug("Configuring task {} of {}".format(id_task+1, len(tasks)) )
            encoder = available_encoders[using](asset, task, job_params)
            result = encoder.configure()

            if not result:
                self.job_fail(job, result.message, critical=True)
                return

            logging.info("Starting task {} of {}".format(id_task+1, len(tasks)) )
            encoder.start()

            old_progress = 0
            while encoder.is_running:
                encoder.work()
                now = time.time()

                if int(now) % 2 == 0:
                    if encoder.progress != old_progress:
                        job.set_progress(encoder.progress, encoder.message)
                        old_progress = encoder.progress

                    stat = job.get_status()
                    if stat == RESTART:
                        encoder.stop()
                        job.restart()
                        return
                    elif stat == ABORTED:
                        encoder.stop()
                        job.abort()
                        return

                if now - last_info_time > FORCE_INFO_EVERY:
                    last_info_time = now
                    logging.debug(
                            "{}: {}, {:.2f}% completed".format(
                            job, encoder.message, encoder.progress
                            ))
                time.sleep(.0001)

            logging.debug("Finalizing task {} of {}".format(id_task+1, len(tasks)))
            result = encoder.finalize()
            if not result:
                job.fail(result.message)
                return
            job_params = encoder.params

        for success_script in action.settings.findall("success"):
            if success_script:
                success_script = success_script.text
                exec(success_script)

        elapsed_time = time.time() - job_start_time
        duration = asset["duration"] or 1
        speed = duration / elapsed_time

        job.done("Finished in {} ({:.02f}x realtime)".format(s2words(elapsed_time), speed))
