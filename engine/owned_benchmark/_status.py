import json,sys,os,datetime as dt
sys.argv=['x','run','--provider',sys.argv[1]]
import importlib.util
spec=importlib.util.spec_from_file_location("ic","inferencecarbon_bench.py")
import inferencecarbon_bench as ic
prov=sys.argv[-1] if False else None
