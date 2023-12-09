import time as time_module
start = time_module.perf_counter()
from functools import lru_cache
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
import os
from random import randrange
import imageio.v3 as iio
import argparse
import mylogger

root = os.getcwd()
VERSION = "1.0rc"
parser = argparse.ArgumentParser(prog=f"duplicateDetector V{VERSION}", description='My duplicate image and video file detector.', epilog="Written by theonlypeti.")

# parser.add_argument("--minimal", action="store_true", help="Quiet mode.")
parser.add_argument("--path", action="store", help="Path to the folder to scan.")
parser.add_argument("--debug", action="store_true", help="Enable debug mode.")
parser.add_argument("--logfile", action="store_true", help="Turns on logging to a text file.")
parser.add_argument("--remove", action="store_true", help="Prompts the user to delete the duplicates.")
parser.add_argument("--no_video", action="store_true", help="Skips videos.")
parser.add_argument("--profiling", action="store_true", help="Measures the runtime and outputs it to profile.prof.")
args = parser.parse_args()

mylogger.main(args)  # initializing the logger
from mylogger import baselogger as logger


# processes = cpu_count()
mappa = args.path or r"Z:/KisPeti/SULI/ipari/p/pc/reddit"


@lru_cache(maxsize=50000) #turns out this does not really help lol
def getsize(i: str):
    return os.path.getsize(i)


def compare(files: str):
    # logger.debug(f"comparing {index} and {index+1} of {len(files)} files")
    # f1 = files[index]
    # f2 = files[index+1]
    f1, f2 = files.split(">")
    try:
        if getsize(f1) == getsize(f2):
            logger.debug(f"{f1=} {f2=}")
            logger.debug(f"f1 size = {getsize(f1) // 1024}kB, f2 size={getsize(f2) // 1024}kB")
            if f1.split(".")[-1] != f2.split(".")[-1]:
                logger.debug("different filetypes")
                return
            try:
                file1 = iio.imread(f1, index=0)
                file2 = iio.imread(f2, index=0)
            except (OSError, IndexError) as e:
                logger.warning(f"OSError: {f1=}, {f2=}\n {e=}")
                return
            else:
                if file1.shape == file2.shape:
                    logger.debug(f"same shape, {file1.shape=}, {file2.shape=}")
                    w = file1.shape[0]
                    h = file1.shape[1]
                    for i in range(10): #10 random pixels
                        randw = randrange(0, w)
                        randh = randrange(0, h)
                        try:
                            if (file1[randw, randh] != file2[randw, randh]).any():
                                logger.debug("different")
                                break
                            else:
                                # print("same")
                                pass
                        except Exception as e:
                            logger.error(f"Exception: {f1=},{f2=},{randh=},{randw=},{file1.shape=},{file2.shape}\n{e=} ")
                            break
                    else:
                        # logger.warning(f"same. remove [{f1}], size {getsize(f1)//1024 + 1}kB")
                        # dupes.append(f"{f1}, size={getsize(f1) // 1024 + 1}kB")
                        return f1, getsize(f1)
                        # totsize += getsize(f1)
                        # os.remove(f2)
    except Exception as e:
        logger.error(f"Exception: {f1=},{f2=}\n{e=}")
        return


def main():
    logger.info(f"Started scanning {mappa}.")
    if not args.remove:
        logger.warning("Not removing duplicates, only listing them. "
                       "Rerun with the --remove flag to be prompted to delete the duplicates.")
    os.chdir(mappa)
    files = list(filter(os.path.isfile, os.listdir()))
    logger.info(f"{len(files)} files found.")

    if args.no_video:
        files = list(filter(lambda f: not f.endswith(".mp4"), sorted(files, key=getsize, reverse=True)))
        logger.info(f"{len(files)} files kept.")
    else:
        files = sorted(files, key=getsize, reverse=True)
    duos = [f"{f1}>{f2}" for f1, f2 in zip(files, files[1:])] #probably terrible? maybe im a genius and i just dont know it

    logger.debug(f"{len(duos)} duos")
    logger.info(f"sorted in {time_module.perf_counter() - start}s")

    with Pool() as pool:
        results = list(tqdm(
            pool.imap_unordered(compare, duos, chunksize=5000),
            total=len(duos),
            colour="CYAN",
            unit="files"
        ))
    dupes = [i[0] for i in results if i]
    sizes = [i[1] for i in results if i]
    totsize = sum(sizes)

    logger.debug(f"{getsize.cache_info()}") #this is for the lru_cache, probably useless as all processes will have their own lru_cache
    logger.info(f"{len(dupes)} duplicates found. \n{totsize//1024} kB total size\n{totsize//1024/1024} MB total size")

    if args.logfile:
        os.chdir(root)
        with open(f".logs/dupes_{time_module.strftime('%m-%d-%H-%M-%S')}.txt", "w") as f:
            f.write("\n".join(dupes))
        os.chdir(mappa)

    if input("YES to print all ") == "YES":
        print(*zip(dupes, sizes), sep="\n")

    if args.remove:
        if input("YES to delete all ") == "YES":
            for i in tqdm(dupes, unit="files"):
                os.remove(i.split(",")[0])


if __name__ == "__main__":
    if args.profiling:
        import cProfile
        import pstats
        with cProfile.Profile() as pr:
            main()
        logger.info(f"{time_module.perf_counter() - start} run time")
        stats = pstats.Stats(pr)
        # stats.sort_stats(pstats.SortKey.TIME)
        # stats.print_stats()
        stats.dump_stats(filename="profile.prof")
        os.system("snakeviz profile.prof")
    else:
        main()
