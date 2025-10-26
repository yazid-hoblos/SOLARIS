import os
import warnings
import logging
mpl_dir = os.path.join(os.getcwd(), 'tmp', 'matplotlib')
os.makedirs(mpl_dir, exist_ok=True)
os.environ.setdefault('MPLCONFIGDIR', mpl_dir)
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib.font_manager")
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
logging.getLogger('matplotlib').setLevel(logging.ERROR)

from main import Main

if __name__ == "__main__":
    process = Main("config/config.json")
    
    while True:
        try:
            cmd = input("run > ")
            result = process.execute(cmd)
            # execute() now returns (success, output, apology)
            if isinstance(result, tuple):
                success, out, apology = result
                if apology:
                    print(apology)
                print(f"$ {cmd}")
                print(out)
            else:
                print(result)
        except KeyboardInterrupt:
            break
        except Exception as e:
            process.logger.error(e)