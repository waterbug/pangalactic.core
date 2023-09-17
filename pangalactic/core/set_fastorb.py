"""
Special module to set pangalactic.core.orb to p.fastorb.orb
"""
import pangalactic.core
from pangalactic.core.fastorb import orb

pangalactic.core.orb = orb

