import app.app as app
import app.config as config
import logging

if __name__ == '__main__':
    """Runs main(). If main returns True, starts the scheduler. If main
       returns False, logs an error and terminates the application.
    """
    import sys
    env_vars = config.init(sys.argv[1:])
    config.logger
    app.main()

    logging.info("------------------------")
    logging.info("App configured as follows:")
    logging.info(config.env_msg)
    logging.info("------------------------")

    try:
        logging.debug("------------------------")
        logging.debug("Starting job scheduler.")
        logging.debug("------------------------")
        config.scheduler.start()
    except KeyboardInterrupt:
        logging.warning("------------------------")
        logging.warning("Scheduled Jobs shut down due to Keyboard Interrupt.")
        logging.warning("------------------------")
        config.scheduler.shutdown()
