"""
Boolean Algebra

Interface Functions:
    num
    var
    comp
    vec
    svec

    factor
    simplify

    nor, nand

    f_not, f_or, f_nor, f_and, f_nand, f_xor, f_xnor, f_implies

    cube_sop
    cube_pos
    iter_space
    iter_points

    uint2vec
    int2vec

Classes:
    Function
        Scalar
            Table
                TruthTable
                ImplicantTable
            Expression
                Numeric: Zero, One
                Symbolic:
                    Literal
                        Variable
                        Complement
                    OrAnd
                        Or
                        And
                    BufNot
                        Buf
                        Not
                    Exclusive
                        Xor
                        Xnor
                    Implies
        Vector

Huntington's Postulates
+---------------------------------+--------------+
| x + y = y + x                   | Commutative  |
| x * y = y * x                   | Commutative  |
+---------------------------------+--------------+
| x + (y * z) = (x + y) * (x + z) | Distributive |
| x * (y + z) = (x * y) + (x * z) | Distributive |
+---------------------------------+--------------+
| x + x' = 1                      | Complement   |
| x * x' = 0                      | Complement   |
+---------------------------------+--------------+

Properties of Boolean Algebraic Systems
+---------------------------+---------------+
| x + (y + z) = (x + y) + z | Associativity |
| x * (y * z) = (x * y) * z | Associativity |
+---------------------------+---------------+
| x + x = x                 | Idempotence   |
| x * x = x                 | Idempotence   |
+---------------------------+---------------+
| x + (x * y) = x           | Absorption    |
| x * (x + y) = x           | Absorption    |
+---------------------------+---------------+
| (x + y)' = x' * y'        | De Morgan     |
| (x * y)' = x' + y'        | De Morgan     |
+---------------------------+---------------+
| (x')' = x                 | Involution    |
+---------------------------+---------------+
"""

__copyright__ = "Copyright (c) 2012, Chris Drake"
__license__ = "All rights reserved."

#==============================================================================
# Constants
#==============================================================================

B = {0, 1}

UNSIGNED, TWOS_COMPLEMENT = range(2)

NUMBERS = dict()
VARIABLES = dict()
COMPLEMENTS = dict()

# Positional Cube Notation
PC_VOID, PC_ONE, PC_ZERO, PC_DC = range(4)

PC_STR = {
    PC_ZERO : "0",
    PC_ONE  : "1",
    PC_DC   : "*"
}

#==============================================================================
# Interface Functions
#==============================================================================

def num(x):
    """Return a unique Boolean number."""
    n = int(x)
    if not n in B:
        raise ValueError("invalid Boolean number: " + str(n))
    try:
        ret = NUMBERS[n]
    except KeyError:
        ret = Numeric(n)
        NUMBERS[n] = ret
    return ret

def var(name, index=-1):
    try:
        ret = VARIABLES[(name, index)]
    except KeyError:
        ret = Variable(name, index)
        VARIABLES[(name, index)] = ret
    return ret

def comp(var):
    try:
        ret = COMPLEMENTS[var]
    except KeyError:
        ret = Complement(var)
        COMPLEMENTS[var] = ret
    return ret

def vec(name, *args, **kwargs):
    """Return a vector of variables."""
    if len(args) == 0:
        raise TypeError("vec() expected at least two argument")
    elif len(args) == 1:
        start, stop = 0, args[0]
    elif len(args) == 2:
        start, stop = args
    else:
        raise TypeError("vec() expected at most three arguments")
    if not 0 <= start < stop:
        raise ValueError("invalid range: [{}:{}]".format(start, stop))
    fs = [Variable(name, index=i) for i in range(start, stop)]
    return Vector(*fs, start=start, **kwargs)

def svec(name, *args, **kwargs):
    """Return a signed vector of variables."""
    return vec(name, *args, bnr=TWOS_COMPLEMENT, **kwargs)

def factor(expr):
    """Return a factored expression."""
    return expr.factor()

def simplify(expr):
    """Return a simplified expression."""
    return expr.simplify()

# operators
def nor(*xs):
    """Boolean NOR (not or) operator"""
    return Not(Or(*xs))

def nand(*xs):
    """Boolean NAND (not and) operator"""
    return Not(And(*xs))

def ite(f, g, h):
    """Boolean ITE (if then else) operator"""
    return Or(And(f, g), And(Not(f), h))

# factored operators
def f_not(x):
    return Not(x).factor()

def f_or(*xs):
    return Or(*xs).factor()

def f_nor(*xs):
    return nor(*xs).factor()

def f_and(*xs):
    return And(*xs).factor()

def f_nand(*xs):
    return nand(*xs).factor()

def f_xor(*xs):
    return Xor(*xs).factor()

def f_xnor(*xs):
    return Xnor(*xs).factor()

def f_implies(x0, x1):
    return Implies(x0, x1).factor()

def cube_sop(*vs):
    """
    Return the multi-dimensional space spanned by N Boolean variables as a
    sum of products.
    """
    points = [p for p in iter_points(And, *vs)]
    return Or(*points)

def cube_pos(*vs):
    """
    Return the multi-dimensional space spanned by N Boolean variables as a
    product of sums.
    """
    points = [p for p in iter_points(Or, *vs)]
    return And(*points)

def iter_space(*vs):
    """Return the multi-dimensional space spanned by N Boolean variables."""
    for n in range(2 ** len(vs)):
        yield [(v if _bit_on(n, i) else -v) for i, v in enumerate(vs)]

def iter_points(op, *vs):
    """
    Iterate through all OR/AND points in the multi-dimensional space spanned
    by N Boolean variables.
    """
    if not issubclass(op, OrAnd):
        raise TypeError("iter_points() expected op type OR/AND")
    for s in iter_space(*vs):
        yield op(*s)

def uint2vec(n, length=None):
    """Convert an unsigned integer to a Vector."""
    assert n >= 0

    vv = Vector()
    if n == 0:
        vv.append(Zero)
    else:
        while n != 0:
            vv.append(num(n & 1))
            n >>= 1

    if length:
        if length < len(vv):
            raise ValueError("overflow: " + str(n))
        else:
            vv.ext(length - len(vv))

    return vv

def int2vec(n, length=None):
    """Convert a signed integer to a Vector."""
    if n < 0:
        req_length = _clog2(abs(n)) + 1
        vv = uint2vec(2 ** req_length + n)
    else:
        req_length = _clog2(n + 1) + 1
        vv = uint2vec(n)
        vv.ext(req_length - len(vv))
    vv.bnr = TWOS_COMPLEMENT

    if length:
        if length < req_length:
            raise ValueError("overflow: " + str(n))
        else:
            vv.ext(length - req_length)

    return vv

#==============================================================================
# Classes
#==============================================================================

class Function:
    """Boolean function"""

    def __abs__(self):
        return len(self.support)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        raise NotImplementedError()

    @property
    def support(self):
        """Return the support of a function.

        Let f(x1, x2, ..., xn) be a Boolean function of N variables. The set
        {x1, x2, ..., xn} is called the *support* of the function.
        """
        raise NotImplementedError()

    @property
    def inputs(self):
        """Return the support as an ordered list."""
        raise NotImplementedError()


class Scalar(Function):
    """Scalar Boolean function"""

    def __neg__(self):
        raise NotImplementedError()

    def __add__(self, other):
        raise NotImplementedError()

    def __mul__(self, other):
        raise NotImplementedError()


class Table(Scalar):
    pass


class TruthTable(Table):

    def __init__(self, inputs, outputs):
        self._inputs = inputs
        self._data = bytearray()
        self._len = 0
        pos = 0
        for pc_val in outputs:
            if pos == 0:
                self._data.append(0)
            self._data[-1] += pc_val << pos
            self._len += 1
            pos = (pos + 2) & 0x07
        assert self._len == 2 ** len(self._inputs)

    def __len__(self):
        return self._len

    def __str__(self):
        s = ["f(" + ", ".join(str(v) for v in self._inputs) + ") = "]
        for i in range(self._len):
            pos = (i & 0x03) << 1
            byte = self._data[(i >> 2)] >> pos
            pc_val = byte & 0x03
            s.append(PC_STR[pc_val])
        return "".join(s)

    @property
    def support(self):
        return set(self._inputs)

    @property
    def inputs(self):
        return self._inputs


class Expression(Scalar):
    """Logic expression"""

    def __init__(self):
        self._cache = dict()

    def __neg__(self):
        return Not(self)

    def __add__(self, other):
        return Or(self, other)

    def __mul__(self, other):
        return And(self, other)

    def __lshift__(self, other):
        return Implies(other, self)

    def __rshift__(self, other):
        return Implies(self, other)

    @property
    def depth(self):
        """The number of levels in the expression tree."""
        raise NotImplementedError()

    def invert(self):
        """Return an inverted expression."""
        raise NotImplementedError()

    def subs(self, d):
        """Substitute numbers into an expression."""
        raise NotImplementedError()

    def vsubs(self, d):
        """Expand all vectors before doing a substitution."""
        return self.subs(_expand_vectors(d))

    def iter_outputs(self):
        for n in range(2 ** abs(self)):
            d = {v: _bit_on(n, i) for i, v in enumerate(self.inputs)}
            yield self.subs(d)

    def to_truth_table(self):
        outputs = ((PC_ONE if x else PC_ZERO) for x in self.iter_outputs())
        return TruthTable(self.inputs, outputs)

    def factor(self):
        """Return a factored expression.

        A factored expression is one and only one of the following:
        * A literal.
        * A sum / product of factored expressions.
        """
        raise NotImplementedError()

    def simplify(self):
        """Return a simplifed expression.

        The meaning of the word "simplified" is not strictly defined here.
        At a bare minimum, operators should apply idempotence, eliminate all
        numbers, eliminate literals that combine into numbers. For factored
        expressions, also absorb terms.
        """
        raise NotImplementedError()

    def iter_cofactors(self, *vs):
        """Iterate through the cofactors of N variables."""
        for n in range(2 ** len(vs)):
            yield self.subs({v: _bit_on(n, i) for i, v in enumerate(vs)})

    def cofactors(self, *vs):
        """Return a list of cofactors of N variables.

        The *cofactor* of f(x1, x2, ..., xi, ..., xn) with respect to
        variable xi is f[xi] = f(x1, x2, ..., 1, ..., xn)

        The *cofactor* of f(x1, x2, ..., xi, ..., xn) with respect to
        variable xi' is f[xi'] = f(x1, x2, ..., 0, ..., xn)
        """
        return [cf for cf in self.iter_cofactors(*vs)]

    def is_neg_unate(self, *vs):
        """Return whether a function is negative unate.

        A function f(x1, x2, ..., xi, ..., xn) is negative unate in variable
        xi if f[xi'] >= f[xi].
        """
        vs = vs or self.inputs
        for v in vs:
            fv0, fv1 = self.cofactors(v)
            if isinstance(fv0, Numeric) or isinstance(fv1, Numeric):
                if not (fv0 is One or fv1 is Zero):
                    return False
            elif not (fv0.minterms >= fv1.minterms):
                return False
        return True

    def is_pos_unate(self, *vs):
        """Return whether a function is positive unate.

        A function f(x1, x2, ..., xi, ..., xn) is positive unate in variable
        xi if f[xi] >= f[xi'].
        """
        vs = vs or self.inputs
        for v in vs:
            fv0, fv1 = self.cofactors(v)
            if isinstance(fv0, Numeric) or isinstance(fv1, Numeric):
                if not (fv1 is One or fv0 is Zero):
                    return False
            elif not (fv1.minterms >= fv0.minterms):
                return False
        return True

    def is_binate(self, *vs):
        """Return whether a function is binate.

        A function f(x1, x2, ..., xi, ..., xn) is binate in variable xi if it
        is neither negative nor positive unate in xi.
        """
        vs = vs or self.inputs
        return not (self.is_neg_unate(*vs) or self.is_pos_unate(*vs))

    def smoothing(self, *vs):
        """Return the smoothing of a function.

        The *smoothing* of f(x1, x2, ..., xi, ..., xn) with respect to
        variable xi is S[xi](f) = f[xi] + f[xi']
        """
        return Or(*self.cofactors(*vs))

    def consensus(self, *vs):
        """Return the consensus of a function.

        The *consensus* of f(x1, x2, ..., xi, ..., xn) with respect to
        variable xi is C[xi](f) = f[xi] * f[xi']
        """
        return And(*self.cofactors(*vs))

    def derivative(self, *vs):
        """Return the derivative of a function.

        The *derivate* of f(x1, x2, ..., xi, ..., xn) with respect to
        variable xi is df/dxi = f[xi] (xor) f[xi']
        """
        return Xor(*self.cofactors(*vs))


class Numeric(Expression):
    """Boolean number"""

    def __init__(self, val):
        super(Numeric, self).__init__()
        self._val = val

    def __bool__(self):
        return bool(self._val)

    def __int__(self):
        return self._val

    def __str__(self):
        return str(self._val)

    def __eq__(self, other):
        if isinstance(other, Expression):
            return isinstance(other, Numeric) and self._val == other.val
        else:
            return self._val == num(other).val

    def __lt__(self, other):
        if isinstance(other, Expression):
            return isinstance(other, Numeric) and self._val < other.val
        else:
            return self._val < num(other).val

    @property
    def support(self):
        return set()

    @property
    def inputs(self):
        return list()

    @property
    def depth(self):
        return 0

    @property
    def val(self):
        return self._val

    def invert(self):
        return num(1 - self._val)

    def subs(self, d):
        return self

    def factor(self):
        return self

    def simplify(self):
        return self


Zero = num(0)
One = num(1)


class Symbolic(Expression):

    def __init__(self):
        super(Symbolic, self).__init__()

    def __iter__(self):
        raise NotImplementedError()

    @property
    def support(self):
        val = self._cache.get("support", None)
        if val is None:
            val = {v for v in self.iter_vars()}
            self._cache["support"] = val
        return val

    @property
    def inputs(self):
        val = self._cache.get("inputs", None)
        if val is None:
            val = sorted(self.support)
            self._cache["inputs"] = val
        return val

    @property
    def top(self):
        """Return the first variable in the ordered support."""
        return self.inputs[0]

    def iter_vars(self):
        """Recursively iterate through all variables in the expression."""
        raise NotImplementedError()

    def iter_minterms(self):
        """Iterate through the sum of products of N literals."""
        for n in range(2 ** abs(self)):
            d = dict()
            space = list()
            for i, v in enumerate(self.inputs):
                on = _bit_on(n, i)
                d[v] = on
                space.append(v if on else -v)
            output = self.subs(d)
            if output:
                yield And(*space)

    def iter_maxterms(self):
        """Iterate through the product of sums of N literals."""
        for n in range(2 ** abs(self)):
            d = dict()
            space = list()
            for i, v in enumerate(self.inputs):
                on = _bit_on(n, i)
                d[v] = on
                space.append(-v if on else v)
            output = self.subs(d)
            if not output:
                yield Or(*space)

    @property
    def minterms(self):
        """The sum of products of N literals"""
        val = self._cache.get("minterms", None)
        if val is None:
            val = {term for term in self.iter_minterms()}
            self._cache["minterms"] = val
        return val

    @property
    def maxterms(self):
        """The product of sums of N literals"""
        val = self._cache.get("maxterms", None)
        if val is None:
            val = {term for term in self.iter_maxterms()}
            self._cache["maxterms"] = val
        return val

    def flatten(self, op):
        """Return expression after flattening OR/AND."""
        expr = self._flatten(op)
        expr = expr.simplify()
        return expr

    def to_sop(self):
        """Return the expression as a sum of products."""
        expr = self.factor()
        expr = expr.flatten(And)
        return expr

    def to_pos(self):
        """Return the expression as a product of sums."""
        expr = self.factor()
        expr = expr.flatten(Or)
        return expr

    def to_csop(self):
        """Return the expression as a sum of products of N literals."""
        return Or(*[term for term in self.iter_minterms()])

    def to_cpos(self):
        """Return the expression as a product of sums of N literals."""
        return And(*[term for term in self.iter_maxterms()])

    def equal(self, other):
        """Return whether this expression is equivalent to another.

        To avoid ambiguity about instantiating multiple variables with the
        same name and index, we are not overloading the __eq__ method to have
        any special meaning. This method provides a convenient way to check
        equivalence when that might not be sufficient.
        """
        raise NotImplementedError()


class Literal(Symbolic):
    """An instance of a variable or of its complement"""

    def __iter__(self):
        yield self

    def __len__(self):
        return 1

    @property
    def depth(self):
        return 0

    @property
    def xs(self):
        return {self}

    def factor(self):
        return self

    def simplify(self):
        return self

    def equal(self, other):
        return self == other


class Variable(Literal):
    """Boolean variable"""

    def __init__(self, name, index=-1):
        super(Variable, self).__init__()
        self._name = name
        self._index = index

    def __str__(self):
        if self._index >= 0:
            return "{0._name}[{0.index}]".format(self)
        else:
            return self._name

    def __lt__(self, other):
        if isinstance(other, Numeric):
            return False
        if isinstance(other, Literal):
            return (self.name < other.name or
                    self.name == other.name and self.index < other.index)
        if isinstance(other, Symbolic):
            return True
        return id(self) < id(other)

    @property
    def name(self):
        return self._name

    @property
    def index(self):
        return self._index

    def iter_vars(self):
        yield self

    def invert(self):
        return comp(self)

    def subs(self, d):
        if self in d:
            val = d[self]
            if not isinstance(val, Scalar):
                val = num(val)
            return val
        else:
            return self


class Complement(Literal):
    """Boolean complement"""

    # Postfix symbol used in string representation
    OP = "'"

    def __init__(self, var):
        super(Complement, self).__init__()
        self._var = var

    def __str__(self):
        return str(self._var) + self.OP

    def __lt__(self, other):
        if isinstance(other, Numeric):
            return False
        if isinstance(other, Variable):
            return (self.name < other.name or
                    self.name == other.name and self.index <= other.index)
        if isinstance(other, Complement):
            return (self.name < other.name or
                    self.name == other.name and self.index < other.index)
        if isinstance(other, Symbolic):
            return True
        return id(self) < id(other)

    @property
    def name(self):
        return self._var.name

    @property
    def index(self):
        return self._var.index

    @property
    def var(self):
        return self._var

    def iter_vars(self):
        yield self._var

    def invert(self):
        return self._var

    def subs(self, d):
        if self._var in d:
            val = d[self._var]
            if not isinstance(val, Scalar):
                val = num(val)
            return Not(val)
        else:
            return self


class OrAnd(Symbolic):
    """base class for Boolean OR/AND expressions"""

    def __new__(cls, *xs):
        temps, xs = list(xs), list()
        # x + (y + z) = (x + y) + z; x * (y * z) = (x * y) * z
        while temps:
            t = temps.pop()
            x = t if isinstance(t, Scalar) else num(t)
            if x == cls.ABSORBER:
                return cls.ABSORBER
            elif isinstance(x, cls):
                temps.extend(x.xs)
            elif x != cls.IDENTITY:
                xs.append(x)

        if len(xs) == 0:
            return cls.IDENTITY
        if len(xs) == 1:
            return xs[0]

        self = super(OrAnd, cls).__new__(cls)
        self.xs = xs
        return self

    def __init__(self, *xs):
        super(OrAnd, self).__init__()

    def __iter__(self):
        return iter(self.xs)

    def __len__(self):
        return len(self.xs)

    def __lt__(self, other):
        if isinstance(other, Numeric):
            return False
        if isinstance(other, Literal):
            return self.support < other.support
        if isinstance(other, self.__class__) and self.depth == other.depth == 1:
            # min/max term
            if self.support == other.support:
                return self.term_index < other.term_index
            else:
                # support containment
                if self.support < other.support:
                    return True
                if other.support < self.support:
                    return False
                # support disjoint
                v = sorted(self.support ^ other.support)[0]
                if v in self.support:
                    return True
                if v in other.support:
                    return False
        return id(self) < id(other)

    @property
    def depth(self):
        val = self._cache.get("depth", None)
        if val is None:
            val = max(x.depth + 1 for x in self.xs)
            self._cache["depth"] = val
        return val

    @property
    def _duals(self):
        val = self._cache.get("duals", None)
        if val is None:
            val = [x for x in self.xs if isinstance(x, self.DUAL)]
            self._cache["duals"] = val
        return val

    def iter_vars(self):
        for x in self.xs:
            if not isinstance(x, Numeric):
                for v in x.iter_vars():
                    yield v

    def invert(self):
        return self.DUAL(*[Not(x) for x in self.xs])

    def subs(self, d):
        replace = list()
        for x in self.xs:
            _x = x.subs(d)
            if id(x) != id(_x):
                replace.append((x, _x))
        if replace:
            xs = self.xs[:]
            for old, new in replace:
                if new == self.ABSORBER:
                    return self.ABSORBER
                else:
                    for i in range(xs.count(old)):
                        xs.remove(old)
                    if new != self.IDENTITY:
                        xs.append(new)
            return self.__class__(*xs)
        else:
            return self

    def factor(self):
        expr = self.__class__(*[x.factor() for x in self.xs])
        return expr.simplify()

    def simplify(self):
        lits, terms, xs = list(), list(), list()

        for x in self.xs:
            x = x.simplify()
            if isinstance(x, Literal):
                lits.append(x)
            elif isinstance(x, self.DUAL) and x.depth == 1:
                terms.append(x)
            else:
                xs.append(x)

        # x + x' = 1; x * x' = 0
        while lits:
            lit = lits.pop()
            if -lit in lits:
                return self.ABSORBER
            else:
                terms.append(lit)

        # Drop all terms that are a subset of other terms
        # x + x = x; x * x = x
        # x + (x * y) = x; x * (x + y) = x
        while terms:
            fst, rst, terms = terms[0], terms[1:], list()
            drop_fst = False
            for term in rst:
                drop_term = False
                if fst.equal(term):
                    drop_term = True
                else:
                    if all(any(fx.equal(tx) for tx in term.xs)
                           for fx in fst.xs):
                        drop_term = True
                    if all(any(fx.equal(tx) for tx in fst.xs)
                           for fx in term.xs):
                        drop_fst = True
                if not drop_term:
                    terms.append(term)
            if not drop_fst:
                xs.append(fst)

        return self.__class__(*xs)

    def _flatten(self, op):
        if isinstance(self, op):
            if self._duals:
                dual = self._duals[0]
                others = [x for x in self.xs if x != dual]
                expr = op.DUAL(*[op(x, *others) for x in dual.xs])
                if isinstance(expr, OrAnd):
                    return expr.flatten(op)
                else:
                    return expr
            else:
                return self
        else:
            nested, others = list(), list()
            for x in self.xs:
                if x.depth > 1:
                    nested.append(x)
                else:
                    others.append(x)
            xs = [x.flatten(op) for x in nested] + others
            return op.DUAL(*xs)

    def equal(self, other):
        assert self.depth == 1
        return (isinstance(other, self.__class__) and self.support == other.support and
                self.term_index == other.term_index)


class Or(OrAnd):
    """Boolean addition (or) operator"""

    # Infix symbol used in string representation
    OP = "+"

    IDENTITY = Zero
    ABSORBER = One

    def __str__(self):
        sep = " " + self.OP + " "
        return sep.join(str(x) for x in sorted(self.xs))

    @property
    def term_index(self):
        n = abs(self) - 1
        idx = 0
        for i, v in enumerate(sorted(self.support)):
            if -v in self.xs:
                idx |= 1 << (n - i)
        return idx


class And(OrAnd):
    """Boolean multiplication (and) operator"""

    # Infix symbol used in string representation
    OP = "*"

    IDENTITY = One
    ABSORBER = Zero

    def __str__(self):
        s = list()
        for x in sorted(self.xs):
            if isinstance(x, Or):
                s.append("(" + str(x) + ")")
            else:
                s.append(str(x))
        sep = " " + self.OP + " "
        return sep.join(s)

    @property
    def term_index(self):
        n = abs(self) - 1
        idx = 0
        for i, v in enumerate(sorted(self.support)):
            if v in self.xs:
                idx |= 1 << (n - i)
        return idx


Or.DUAL = And
And.DUAL = Or


class BufNot(Symbolic):
    """base class for BUF/NOT operators"""

    def __init__(self, x):
        super(BufNot, self).__init__()
        self.x = x if isinstance(x, Scalar) else num(x)

    @property
    def depth(self):
        return self.x.depth

    @property
    def xs(self):
        return {self.x}

    def iter_vars(self):
        for v in self.x.iter_vars():
            yield v

    def subs(self, d):
        expr = self.x.subs(d)
        if id(expr) == id(self.x):
            return self
        else:
            return self.__class__(expr)

    def simplify(self):
        expr = self.x.simplify()
        if id(expr) == id(self.x):
            return self
        else:
            return self.__class__(expr)


class Buf(BufNot):
    """buffer operator"""

    def __new__(cls, x):
        x = x if isinstance(x, Scalar) else num(x)
        # Auto-simplify numbers and literals
        if isinstance(x, Numeric) or isinstance(x, Literal):
            return x
        else:
            return super(Buf, cls).__new__(cls)

    def __str__(self):
        return "Buf({0.x})".format(self)

    def factor(self):
        return self.x.factor()


class Not(BufNot):
    """Boolean NOT operator"""

    def __new__(cls, x):
        x = x if isinstance(x, Scalar) else num(x)
        # Auto-simplify numbers and literals
        if isinstance(x, Numeric) or isinstance(x, Literal):
            return x.invert()
        else:
            return super(Not, cls).__new__(cls)

    def __str__(self):
        return "Not({0.x})".format(self)

    def factor(self):
        # Get rid of unfactored expressions first, then invert and refactor.
        return self.x.factor().invert().factor()


class Exclusive(Symbolic):
    """Boolean exclusive (XOR, XNOR) operator"""

    IDENTITY = Zero

    def __new__(cls, *xs):
        parity = cls.PARITY
        temps, xs = list(xs), list()
        while temps:
            t = temps.pop()
            x = t if isinstance(t, Scalar) else num(t)
            if x is One:
                parity ^= 1
            elif isinstance(x, cls):
                temps.extend(x.xs)
            elif x != cls.IDENTITY:
                xs.append(x)

        if len(xs) == 0:
            return Not(cls.IDENTITY) if parity else cls.IDENTITY
        if len(xs) == 1:
            return Not(xs[0]) if parity else xs[0]

        self = super(Exclusive, cls).__new__(cls)
        self.xs = xs
        self._parity = parity
        return self

    def __init__(self, *xs):
        super(Exclusive, self).__init__()

    def __iter__(self):
        return iter(self.xs)

    def __len__(self):
        return len(self.xs)

    def __str__(self):
        args = ", ".join(str(x) for x in self.xs)
        if self._parity:
            return "Xnor(" + args + ")"
        else:
            return "Xor(" + args + ")"

    @property
    def depth(self):
        val = self._cache.get("depth", None)
        if val is None:
            val = max(x.depth + 2 for x in self.xs)
            self._cache["depth"] = val
        return val

    def iter_vars(self):
        for x in self.xs:
            if not isinstance(x, Numeric):
                for v in x.iter_vars():
                    yield v

    def subs(self, d):
        replace = list()
        for x in self.xs:
            _x = x.subs(d)
            if id(x) != id(_x):
                replace.append((x, _x))
        if replace:
            xs = self.xs[:]
            parity = self._parity
            for old, new in replace:
                for i in range(xs.count(old)):
                    xs.remove(old)
                if new is One:
                    parity ^= 1
                elif new != self.IDENTITY:
                    xs.append(new)
            return Xnor(*xs) if parity else Xor(*xs)
        else:
            return self

    def factor(self):
        x, xs = self.xs[0], self.xs[1:]
        expr = Or(And(Not(x), Xor(*xs)), And(x, Xnor(*xs)))
        if self._parity:
            return Not(expr).factor()
        else:
            return expr.factor()

    def simplify(self):
        parity = self._parity

        lits, xs = list(), list()
        for x in self.xs:
            x = x.simplify()
            if isinstance(x, Literal):
                lits.append(x)
            else:
                xs.append(x)

        while lits:
            x = lits.pop()
            # XOR(x, x) = 0
            if x in lits:
                lits.remove(x)
            # XOR(x, x') = 1
            elif -x in lits:
                lits.remove(-x)
                parity ^= 1
            else:
                xs.append(x)

        return Xnor(*xs) if parity else Xor(*xs)


class Xor(Exclusive):
    PARITY = 0


class Xnor(Exclusive):
    PARITY = 1


class Implies(Symbolic):
    """Boolean implication operator"""

    OP = "=>"

    def __new__(cls, x0, x1):
        xs = [x if isinstance(x, Scalar) else num(x) for x in (x0, x1)]
        # 0 => x = 1; x => 1 = 1
        if xs[0] is Zero or xs[1] is One:
            return One
        # 1 => x = x
        elif xs[0] is One:
            return xs[1]
        # x => 0 = x'
        elif xs[1] is Zero:
            return Not(xs[0])
        else:
            self = super(Implies, cls).__new__(cls)
            self.xs = xs
            return self

    def __init__(self, x0, x1):
        super(Implies, self).__init__()

    def __str__(self):
        s = list()
        for x in self.xs:
            if isinstance(x, Implies):
                s.append("(" + str(x) + ")")
            else:
                s.append(str(x))
        sep = " " + self.OP + " "
        return sep.join(s)

    @property
    def depth(self):
        val = self._cache.get("depth", None)
        if val is None:
            val = max(x.depth + 1 for x in self.xs)
            self._cache["depth"] = val
        return val

    def iter_vars(self):
        for x in self.xs:
            for v in x.iter_vars():
                yield v

    def factor(self):
        return Or(Not(self.xs[0]), self.xs[1]).factor()

    def simplify(self):
        xs = [x.simplify() for x in self.xs]

        # x => x = 1
        if xs[0] == xs[1]:
            return One
        # -x => x = x; x => -x = -x
        elif -xs[0] == xs[1] or xs[0] == -xs[1]:
            return xs[1]

        return Implies(xs[0], xs[1])


class Vector(Function):
    """Vector Boolean function"""

    def __init__(self, *fs, **kwargs):
        self.fs = [f if isinstance(f, Scalar) else num(f) for f in fs]
        self._start = kwargs.get("start", 0)
        self._bnr = kwargs.get("bnr", UNSIGNED)

    def __len__(self):
        return len(self.fs)

    def __int__(self):
        return self.to_int()

    def __str__(self):
        return str(self.fs)

    def __iter__(self):
        for f in self.fs:
            yield f

    # unary operators
    def __invert__(self):
        fs = [Not(v) for v in self.fs]
        return Vector(*fs, start=self._start, bnr=self._bnr)

    def uor(self):
        return Or(*list(self.fs))

    def uand(self):
        return And(*list(self.fs))

    def uxor(self):
        return Xor(*list(self.fs))

    # binary operators
    def __or__(self, other):
        assert isinstance(other, Vector) and len(self) == len(other)
        return Vector(*[Or(*t) for t in zip(self.fs, other.fs)])

    def __and__(self, other):
        assert isinstance(other, Vector) and len(self) == len(other)
        return Vector(*[And(*t) for t in zip(self.fs, other.fs)])

    def __xor__(self, other):
        assert isinstance(other, Vector) and len(self) == len(other)
        return Vector(*[Xor(*t) for t in zip(self.fs, other.fs)])

    def getifz(self, i):
        """Get item from zero-based index."""
        return self.__getitem__(i + self.start)

    def __getitem__(self, sl):
        if isinstance(sl, int):
            return self.fs[self._norm_idx(sl)]
        else:
            norm = self._norm_slice(sl)
            return Vector(*self.fs.__getitem__(norm),
                          start=(norm.start + self._start),
                          bnr=self._bnr)

    def __setitem__(self, sl, f):
        if isinstance(sl, int):
            self.fs.__setitem__(sl, f)
        else:
            norm = self._norm_slice(sl)
            self.fs.__setitem__(norm, f)

    @property
    def start(self):
        return self._start

    @property
    def bnr(self):
        return self._bnr

    @bnr.setter
    def bnr(self, value):
        self._bnr = value

    @property
    def sl(self):
        return slice(self._start, len(self.fs) + self._start)

    def to_uint(self):
        """Convert vector into an unsigned integer."""
        n = 0
        for i, f in enumerate(self.fs):
            if isinstance(f, Numeric):
                if f is One:
                    n += 2 ** i
            else:
                raise ValueError("cannot convert to uint")
        return n

    def to_int(self):
        """Convert vector into an integer."""
        n = self.to_uint()
        if self._bnr == TWOS_COMPLEMENT and self.fs[-1]:
            return -2 ** self.__len__() + n
        else:
            return n

    def subs(self, d):
        """Substitute numbers into a Boolean vector."""
        cpy = self[:]
        for i, f in enumerate(cpy.fs):
            cpy[i] = cpy[i].subs(d)
        return cpy

    def vsubs(self, d):
        """Expand all vectors before doing a substitution."""
        return self.subs(_expand_vectors(d))

    def append(self, f):
        """Append logic function to the end of this vector."""
        self.fs.append(f)

    def ext(self, n):
        """Extend this vector by N bits.

        If this vector uses two's complement representation, sign extend;
        otherwise, zero extend.
        """
        if self.bnr == TWOS_COMPLEMENT:
            bit = self.fs[-1]
        else:
            bit = Zero
        for i in range(n):
            self.append(bit)

    def eq(A, B):
        assert isinstance(B, Vector) and len(A) == len(B)
        return And(*[Xnor(*t) for t in zip(A.fs, B.fs)])

    def decode(A):
        return Vector(*[And(*[f if _bit_on(i, j) else -f
                              for j, f in enumerate(A.fs)])
                        for i in range(2 ** len(A))])

    def ripple_carry_add(A, B, ci=Zero):
        assert isinstance(B, Vector) and len(A) == len(B)
        if A.bnr == TWOS_COMPLEMENT or B.bnr == TWOS_COMPLEMENT:
            sum_bnr = TWOS_COMPLEMENT
        else:
            sum_bnr = UNSIGNED
        S = Vector(bnr=sum_bnr)
        C = Vector()
        for i, A in enumerate(A.fs):
            carry = (ci if i == 0 else C[i-1])
            S.append(Xor(A, B.getifz(i), carry))
            C.append(A * B.getifz(i) + A * carry + B.getifz(i) * carry)
        return S, C

    def _norm_idx(self, i):
        """Return an index normalized to vector start index."""
        if i >= 0:
            if i < self._start:
                raise IndexError("list index out of range")
            else:
                idx = i - self._start
        else:
            idx = i + self._start
        return idx

    def _norm_slice(self, sl):
        """Return a slice normalized to vector start index."""
        d = dict()
        for k in ("start", "stop"):
            idx = getattr(sl, k)
            if idx is not None:
                d[k] = (idx if idx >= 0 else self.sl.stop + idx)
            else:
                d[k] = getattr(self.sl, k)
        if d["start"] < self.sl.start or d["stop"] > self.sl.stop:
            raise IndexError("list index out of range")
        elif d["start"] >= d["stop"]:
            raise IndexError("zero-sized slice")
        return slice(d["start"] - self._start, d["stop"] - self._start)


#==============================================================================
# Internal Functions
#==============================================================================

def _clog2(n):
    """Return the ceiling, log base two of an integer."""
    assert n >= 1
    i, x = 0, 1
    while x < n:
        x = x << 1;
        i += 1
    return i

def _bit_on(n, bit):
    return bool((n >> bit) & 1)

def _expand_vectors(d):
    """Expand all vectors in a substitution dict."""
    temp = {k: v for k, v in d.items() if isinstance(k, Vector)}
    d = {k: v for k, v in d.items() if k not in temp}
    while temp:
        key, val = temp.popitem()
        if isinstance(key, Vector):
            assert len(key) == len(val)
            for i, x in enumerate(val):
                d[key.getifz(i)] = x if isinstance(x, Scalar) else num(x)
        elif isinstance(key, Literal):
            d[key] = val
    return d
