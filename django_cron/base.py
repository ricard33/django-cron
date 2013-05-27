"""
Copyright (c) 2007-2008, Dj Gilcrease
All rights reserved.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""
import cPickle
from threading import Timer
from datetime import datetime, tzinfo

from django.dispatch import dispatcher
from django.conf import settings

from signals import cron_done
import models

# how often to check if jobs are ready to be run (in seconds)
# in reality if you have a multithreaded server, it may get checked
# more often that this number suggests, so keep an eye on it...
# default value: 300 seconds == 5 min
polling_frequency = getattr(settings, "CRON_POLLING_FREQUENCY", 300)

class Job(object):
    # 86400 seconds == 24 hours
    run_every = 86400

    def run(self, *args, **kwargs):  
        self.job()
        cron_done.send(sender=self, *args, **kwargs)

    def job(self):
        """
        Should be overridden (this way is cleaner, but the old way - overriding run() - will still work)
        """
        pass

    def whoami(self):
        """Returns the string of the full name of this class (with module path)."""
        return "%s.%s" % (self.__module__, self.__class__.__name__)

class CronScheduler(object):
    def register(self, job_class, *args, **kwargs):
        """
        Register the given Job with the scheduler class
        """

        job_instance = job_class()

        if not isinstance(job_instance, Job):
            raise TypeError("You can only register a Job not a %r" % job_class)

        job, created = models.Job.objects.get_or_create(name=str(job_instance.whoami()))
        if created:
            job.instance = cPickle.dumps(job_instance)
        job.args = cPickle.dumps(args)
        job.kwargs = cPickle.dumps(kwargs)
        job.run_frequency = job_instance.run_every
        job.queued = True
        job.save()

    def start(self):
        t = Timer(0, self.__execute)
        t.setDaemon(True)
        t.start()

    def __execute(self):
        """
        Queue all Jobs for execution
        """
        status, created = models.Cron.objects.get_or_create(pk=1)

        # This is important for 2 reasons:
        #     1. It keeps us for running more than one instance of the
        #        same job at a time
        #     2. It reduces the number of polling threads because they
        #        get killed off if they happen to check while another
        #        one is already executing a job (only occurs with
        #		 multi-threaded servers)
        if status.executing:
            return

        status.executing = True
        try:
            status.save()
        except:
            # this will fail if you're debugging, so we want it
            # to fail silently and start the timer again so we 
            # can pick up where we left off once debugging is done
            Timer(polling_frequency, self.__execute).start()
            return

        jobs = models.Job.objects.all()
        for job in jobs:

            if job.queued:
                tz = job.last_run.tzinfo
                if tz:
                    now = datetime.now(tz=tz)
                else:
                    now = datetime.now()

                time_delta = now - job.last_run
                if (time_delta.seconds + 86400*time_delta.days) > job.run_frequency:
                    try:
                        inst = cPickle.loads(str(job.instance))
                        args = cPickle.loads(str(job.args))
                        kwargs = cPickle.loads(str(job.kwargs))
                    except Exception:
                        import logging
                        logging.exception("Can't load job '%s'. Deleting references." % job.name)
                        job.delete()
                        continue

                    try:
                        inst.run(*args, **kwargs)
                        from django.utils.timezone import UTC
                        job.last_run = datetime.now(tz=settings.USE_TZ and UTC() or None)
                        job.save()

                    except Exception:
                        import logging
                        logging.exception("Failed to execute job '%s'. Job disabled." % job.name)
                        # if the job throws an error, just remove it from
                        # the queue. That way we can find/fix the error and
                        # requeue the job manually
                        job.queued = False
                        job.save()

        status.executing = False
        status.save()

        # Set up for this function to run again
        Timer(polling_frequency, self.__execute).start()

    def cleanup_old_jobs(self):
        jobs = models.Job.objects.all()
        for job in jobs:
            try:
                module_name, cl = job.name.rsplit('.', 1)
                import imp, sys
                try:
                    mod = sys.modules[module_name]
                except KeyError:
                    mod = __import__(module_name)
                if cl not in dir(mod):
                    import logging
                    logging.error("Failed to find job '%s'. Job removed." % job.name)
                    job.delete()

            except ValueError:
                import logging
                logging.error("Failed to unpack job's name '%s'. Job removed." % job.name)
                job.delete()
            except ImportError:
                import logging
                logging.error("Failed to import job '%s'. Job removed." % job.name)
                job.delete()



cronScheduler = CronScheduler()
