# -*- coding: utf-8 -*-
import logging
import os.path

log = logging.getLogger('nens.symbol_manager')

class SymbolManager:
    def __init__(self, symbol_path):
        log.debug('Initializing SymbolManager')
        self.symbol_path = symbol_path
        if not(os.path.exists(self.symbol_path)):
            log.critical('path %s does not exist'%self.symbol_path)
            raise Exception('SymbolManager failed: path %s does not exist'%self.symbol_path)

    def get_symbol_transformed(self, filename_nopath, **kwargs):
        """Returns filename with abs path of transformed symbol,

        if the transformed symbol does not yet exist, it is created. Transformation
        as follows:
        1) colorize, if given
        2) scale, if given
        3) rotate, if given

        input: filename_nopath is <symbol_path>\originals\<filename_nopath>
        kwargs:
        * size: (<x>, <y>)
        * colorize: (r, g, b) (alpha is unaltered)
        * rotate: in degrees, counterclockwise, around center
        """
        log.debug('Entering get_symbol_transformed')

        result_filename = os.path.join(self.symbol_path, 'generated/', '')
        if os.path.isfile(result_filename):
            log.debug('image already exists, returning filename')
            return result_filename
        else:
            log.debug('generating image...')
            #filename_abs = os.path.join(self.symbol_path, 'originals/', filename_nopath)


if __name__=='__main__':
    #set log level to debug
    log.setLevel(logging.DEBUG)

    #create a console handler for logger
    h = logging.StreamHandler()
    h.setLevel(logging.DEBUG)
    #formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    h.setFormatter(formatter)
    logging.getLogger('').addHandler(h)

    #start testing
    log.info('Testing SymbolManager...')
    sm = SymbolManager('/media/drv0/repo/Products/LizardWeb/Trunk/System/resources/symbols')
