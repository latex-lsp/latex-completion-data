import logging
from timeit import default_timer as timer
import symbols
import tex
import util
import components


def main():
    logging.basicConfig(format='%(levelname)-8s %(message)s',
                        level=logging.INFO, filename='latex-completion-data.log', filemode='w')

    start_time = timer()
    component_database = components.generate_database()
    symbol_database = symbols.render_database()
    end_time = timer()

    logging.info('Elapsed time: %d seconds', end_time - start_time)


if __name__ == '__main__':
    main()
