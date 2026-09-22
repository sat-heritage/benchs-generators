"""Print, for each CNF file, its GBD hash, isohash2, variable and clause counts."""
import sys, gbdc

for path in sys.argv[1:]:
    feats = gbdc.extract_base_features(path)
    print("\t".join([path, gbdc.gbdhash(path), gbdc.isohash2(path),
                     str(int(feats.get("variables", -1))), str(int(feats.get("clauses", -1)))]))
