import bottle
import logging

logger = logging.getLogger(__name__)


class SnapServer(object):
    def __init__(self, robot,
                 host, port,
                 quiet=True, server='tornado'):
        self.robot = robot
        self.host = host
        self.port = port
        self.quiet = quiet
        self.server = server

        self.app = bottle.Bottle()

        @self.app.get('/<motor>/<register>')
        def get(motor, register):
            m = getattr(self.robot, motor)
            s = str(getattr(m, register))

            r = bottle.response

            r.status = '200 OK'
            r.set_header('Content-Type', 'text/html')
            r.set_header('charset', 'ISO-8859-1')
            r.set_header('Content-Length', len(s))
            r.set_header('Access-Control-Allow-Origin', '*')

            logger.info('Get %s.%s', motor, register)

            return s

        @self.app.get('/<motor>/<register>/<value>')
        def set(motor, register, value):
            m = getattr(self.robot, motor)
            setattr(m, register, float(value))

            logger.info('Set %s.%s = %s', motor, register, value)

    def run(self):
        bottle.run(self.app,
                   host=self.host, port=self.port,
                   quiet=self.quiet, server=self.server)


if __name__ == '__main__':
    import time
    import platform
    import logging.config

    import pypot.robot

    from pypot.robot.config import ergo_robot_config

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,

        'formatters': {
            'normal': {
                'format': '%(asctime)s %(message)s',
            },
        },
        'handlers': {
            'file': {
                'level': 'DEBUG',
                'class': 'logging.FileHandler',
                'filename': 'snap.log',
                'formatter': 'normal'
            }
        },
        'loggers': {
            'pypot.server.snapserver': {
                'handlers': ['file', ],
                'level': 'DEBUG',
            },
        },
    }

    logging.config.dictConfig(LOGGING)

    arm_config = ergo_robot_config.copy()

    port = '/dev/ttyUSB0' if platform.system() == 'linux' else '/dev/tty.usbserial-A4012ACT'
    arm_config['controllers']['my_dxl_controller']['port'] = port

    arm_config['motors']['gripper'] = {'angle_limit': (-90, -50),
                                       'id': 17,
                                       'offset': 0,
                                       'orientation': 'direct',
                                       'type': 'RX-28'}

    arm_config['controllers']['my_dxl_controller']['attached_motors'].append('gripper')

    arm_config['motors']['base_pan']['offset'] = -22.5
    arm_config['motors']['base_tilt_lower']['offset'] = -22.5
    arm_config['motors']['base_tilt_upper']['offset'] = -22.5
    arm_config['motors']['head_pan']['offset'] = -22.5
    arm_config['motors']['gripper']['offset'] = -90.0

    arm = pypot.robot.from_config(arm_config)
    # arm.start_sync()

    # for m in arm.motors:
    #     m.compliant = False
    #     m.moving_speed = 100
    #     m.goal_position = 0

    # time.sleep(1)

    server = SnapServer(arm, '127.0.0.1', 8080, quiet=False, server='tornado')
    server.run()
