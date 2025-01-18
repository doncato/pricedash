from flask_sqlalchemy import SQLAlchemy

from .models import base
from .models import *

from .manager import *

from .schemas import *

db = SQLAlchemy(model_class=base)