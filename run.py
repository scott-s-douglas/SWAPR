from __future__ import division, print_function
from SWAPRsqlite import *
from SWAPRrubric import *
from SWAPRweights import *
from SWAPRgrades import *
from itertools import groupby
from numpy import median, mean


db = SqliteDB("AnonymousCampus.sqlite")
db.cursor.execute("DELETE FROM WEIGHTS where WEIGHTTYPE = ?", ["gaussian"])
db.conn.commit()
assignGaussianWeights(db, 1, 5)
assignGaussianWeights(db, 2, 5)
assignGaussianWeights(db, 3, 5)
setGradeGaussian(db, 1, "gaussian")
setGradeGaussian(db, 2, "gaussian")
setGradeGaussian(db, 3, "gaussian")
db.conn.commit()
#assignWeightedGrade(db, 1)
