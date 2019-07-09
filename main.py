import logging
from time import time


def main():
    logging.basicConfig(
        format='%(levelname)-8s %(message)s', level=logging.DEBUG)

    start_time = time()
    print('Hello World!')
    end_time = time()

    logging.info('Elapsed time: %d seconds', end_time - start_time)


if __name__ == '__main__':
    main()
