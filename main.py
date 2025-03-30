import time as time_module
from collections import defaultdict
from functools import lru_cache
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
import os
from random import randrange
import imageio.v3 as iio
import argparse
import utils.mylogger as mylogger
start = time_module.perf_counter()

root = os.getcwd()
VERSION = "1.1"
parser = argparse.ArgumentParser(prog=f"duplicateDetector V{VERSION}", description='My duplicate image and video file detector.', epilog="Written by theonlypeti.")

# parser.add_argument("--minimal", action="store_true", help="Quiet mode.")
parser.add_argument("--path", action="store", help="Path to the folder to scan.", required=True)
parser.add_argument("--remove", action="store_true", help="Prompts the user to delete the duplicates.")
parser.add_argument("--date", action="store", help="Date and time (yyyy.mm.dd hh:mm), where files only added after this are checked for duplicates.")
parser.add_argument("--debug", action="store_true", help="Enable debug mode.")
parser.add_argument("--logfile", action="store_true", help="Turns on logging to a text file.")
parser.add_argument("--no_video", action="store_true", help="Skips videos.")
parser.add_argument("--profiling", action="store_true", help="Measures the runtime and outputs it to profile.prof.")
parser.add_argument("--number", action="store", help="Limit how many files to scan (benchmark).")
parser.add_argument("--cpus", action="store", help="Limit how many processes to spin up (benchmark).")
parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
args = parser.parse_args()

mylogger.main(args)  # initializing the logger
from utils.mylogger import baselogger as logger


# processes = cpu_count()
mappa = args.path or r"Z:/KisPeti/SULI/ipari/p/pc/insta"


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


# import hashlib
#
# def get_hash(file_path):
#     with open(file_path, 'rb') as file:
#         data = file.read()
#     return hashlib.md5(data).hexdigest()
#
# def compare(files: str):
#     f1, f2 = files.split(">")
#     try:
#         if get_hash(f1) == get_hash(f2):
#             return f1, getsize(f1)
#     except Exception as e:
#         logger.error(f"Exception: {f1=},{f2=}\n{e=}")
#         return


def main():
    logger.info(f"Started scanning {mappa}.")
    if not args.remove:
        logger.warning("Not removing duplicates, only listing them. "
                       "Rerun with the --remove flag to be prompted to delete the duplicates.")
    os.chdir(mappa)
    if args.date:
        logger.info(f"Only files added after {args.date} will be checked.")
        try:
            tmstmp = time_module.mktime(time_module.strptime(args.date, "%Y.%m.%d %H:%M"))
        except ValueError:
            tmstmp = time_module.mktime(time_module.strptime(args.date, "%Y.%m.%d"))

        newfiles = list(filter(lambda f: os.path.getctime(f) > tmstmp, os.listdir()))
        newsizes = {getsize(i) for i in newfiles}
        logger.info(f"{len(newfiles)} files added after {args.date}.")
        files = list(filter(lambda f: getsize(f) in newsizes, os.listdir()))
        logger.debug(f"{len(newfiles)=}\n{len(newsizes)=}\n{newsizes=}\n{len(files)=}")
    else:
        files = list(filter(os.path.isfile, os.listdir()))
        if args.number:
            files = files[:int(args.number)]
    logger.info(f"{len(files)-1} comparsions found.") #-1 because of the duos to compare, the users would be confused otherwise why the progress bar does not correspond to the number of files

    if args.cpus:
        cpus = int(args.cpus)
    else:
        cpus = cpu_count()


    if args.no_video:
        files = list(filter(lambda f: not f.endswith(".mp4"), sorted(files, key=getsize, reverse=True)))
        logger.info(f"{len(files)} files kept.")
    else:
        files = sorted(files, key=getsize, reverse=True)
    duos = [f"{f1}>{f2}" for f1, f2 in zip(files, files[1:])] #probably terrible? i could just use a list of tuples

    logger.debug(f"{len(duos)} duos")
    logger.info(f"sorted in {time_module.perf_counter() - start}s")

    with Pool(processes=cpus) as pool:
        results = list(tqdm(
            pool.imap_unordered(compare, duos, chunksize=100),
            total=len(duos),
            colour="CYAN",
            unit="files"
        ))
    dupes = [i[0] for i in results if i]
    sizes = [i[1] for i in results if i]
    totsize = sum(sizes)

    logger.debug(f"{getsize.cache_info()}") #this is for the lru_cache, probably useless as all processes will have their own lru_cache
    logger.info(f"{len(dupes)} duplicates found. \n{totsize//1024} kB total size\n{totsize//1024/1024} MB total size")
    logger.handlers[0].flush()

    if args.logfile:
        os.chdir(root)
        with open(f".logs/dupes_{time_module.strftime('%m-%d-%H-%M-%S')}.txt", "w") as f:
            f.write("\n".join(dupes))
        os.chdir(mappa)

    if input("YES to print all ") == "YES":
        # print(*zip(dupes, sizes), sep="\n")
        counter = defaultdict(int)
        for i in dupes:
            name = i.split("-")[0]
            counter[name] += 1
        print(*counter.items(), sep="\n")


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
