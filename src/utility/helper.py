from logging import getLogger
from typing import Iterable
from math import log1p
logger=getLogger("helper")

def infer_programming_language(files:Iterable[str],threshold:float=0.35)->list[str]:
        suffix_count:dict[str,int]=dict()
        fs=set(files)
        tot_files=len(fs)
        ret_suffixes=list()
        for file in fs:
            try:
                suffix=file.rsplit(".",maxsplit=1)[1]
                if suffix not in suffix_count:
                    suffix_count[suffix]=0
                suffix_count[suffix]+=1
            except IndexError:
                pass
        for suff,count in suffix_count.items():
            logger.debug(f"Found suffix {suff} {count} times on {tot_files} files")
            if float(count/tot_files) >= threshold:
                ret_suffixes.append("."+suff)
        return ret_suffixes
