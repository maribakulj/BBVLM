"""Same A79 algorithm, separate outputs after pre-inference environment failure."""
import merge_yolo_regions_a79 as run
run.OUT = run.OUT / 'retry'
if __name__ == '__main__': run.main()
