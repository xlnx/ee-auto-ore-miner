import sys
import yaml
import logging
import argparse
from .config import config

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--config', required=True, action='store',
                    help='path to yaml config file')

args = parser.parse_args()


file_handler = logging.FileHandler(filename='miner.log', encoding='utf-8')
stdout_handler = logging.StreamHandler(sys.stdout)
handlers = [file_handler, stdout_handler]
logging.basicConfig(
    level=logging.INFO,
    format=u'[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
    handlers=handlers,
    force=True
)

with open(args.config, 'r', encoding='utf-8') as f:
    _CONFIG = yaml.load(f.read(), Loader=yaml.FullLoader)

config.load(_CONFIG)

if __name__ == "__main__":
    from .impl import main
    main()
