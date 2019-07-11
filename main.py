import logging
from timeit import default_timer as timer
import symbols
import tex


def main():
    logging.basicConfig(
        format='%(levelname)-8s %(message)s', level=logging.DEBUG)

    start_time = timer()
    print('Hello World!')
    end_time = timer()

    logging.info('Elapsed time: %d seconds', end_time - start_time)


if __name__ == '__main__':
    main()
