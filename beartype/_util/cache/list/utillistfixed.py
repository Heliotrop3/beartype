#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright (c) 2014-2020 Cecil Curry.
# See "LICENSE" for further details.

'''
**Fixed list type** (i.e., :class:`list` subclass constrained to a fixed length
defined at instantiation time).**

This private submodule is *not* intended for importation by downstream callers.
'''

# ....................{ IMPORTS                           }....................
from beartype.roar import _BeartypeUtilCachedFixedListException
from beartype._util.utilstr import trim_object_repr
from collections.abc import Iterable, Sized

# See the "beartype.__init__" submodule for further commentary.
__all__ = ['STAR_IMPORTS_CONSIDERED_HARMFUL']

# ....................{ TODO                              }....................
#FIXME: Consider submitting this type as a relevant StackOverflow answer: e.g.,
#    https://stackoverflow.com/questions/10617045/how-to-create-a-fix-size-list-in-python
#    https://stackoverflow.com/questions/51558015/implementing-efficient-fixed-size-fifo-in-python

# ....................{ CLASSES                           }....................
#FIXME: Override the superclass:
#
#* __reduce_ex__() dunder method to pickle this fixed list. Avoid defining the
#  __reduce__() dunder method, which has been entirely obsoleted by
#  __reduce_ex__().
class FixedList(list):
    '''
    **Fixed list** (i.e., :class:`list` constrained to a fixed length defined
    at instantiation time).**

    A fixed list is effectively a mutable tuple. Whereas a tuple is immutable
    and thus prohibits changes to its contained items, a fixed list is mutable
    and thus *permits* changes to its contained items.

    Design
    ----------
    This list enforces this constraint by overriding *all* :class:`list` dunder
    and standard methods that would otherwise modify the length of this list
    (e.g., :meth:`list.__delitem__`, :meth:`list.append`) to instead
    unconditionally raise an :class:`_BeartypeUtilCachedFixedListException`
    exception.
    '''

    # ..................{ CLASS VARIABLES                   }..................
    # Slot *ALL* instance variables defined on this object to minimize space
    # and time complexity across frequently called @beartype decorations.
    __slots__ = ()

    # ..................{ INITIALIZER                       }..................
    def __init__(self, size: int) -> None:
        '''
        Initialize this fixed list to the passed length and all items of this
        fixed list to ``None``.

        Parameters
        ----------
        size : IntType
            Length to constrain this fixed list to.

        Raises
        ----------
        _BeartypeUtilCachedFixedListException
            If this length is either not an integer *or* is but is
            **non-positive** (i.e., is less than or equal to 0).
        '''

        # If this length is *NOT* an integer, raise an exception.
        if not isinstance(size, int):
            raise _BeartypeUtilCachedFixedListException(
                'Fixed list length {!r} not integer.'.format(size))
        # Else, this length is an integer.

        # If this length is non-positive, raise an exception.
        if size <= 0:
            raise _BeartypeUtilCachedFixedListException(
                'Fixed list length {!r} <= 0.'.format(size))
        # Else, this length is positive.

        # Make it so with the standard Python idiom for preallocating list
        # space -- which, conveniently, is also the optimally efficient means
        # of doing so. See also the timings in this StackOverflow answer:
        #     https://stackoverflow.com/a/10617221/2809027
        super().__init__([None]*size)

    # ..................{ GOOD ~ non-dunders                }..................
    # Permit non-dunder methods preserving list length but otherwise requiring
    # overriding.

    def copy(self) -> 'FixedList':

        # Nullified fixed list of the same length as this fixed list.
        list_copy = FixedList(len(self))

        # Slice over the nullified contents of this copy with those of this
        # fixed list.
        list_copy[:] = self

        # Return this copy.
        return list_copy

    # ..................{ BAD ~ dunders                     }..................
    # Prohibit dunder methods modifying list length by overriding these methods
    # to raise exceptions.

    def __delitem__(self, index):
        raise _BeartypeUtilCachedFixedListException(
            '{} index {!r} not deletable.'.format(self._label, index))


    def __iadd__(self, value):
        raise _BeartypeUtilCachedFixedListException(
            '{} not addable by {}.'.format(
                self._label, trim_object_repr(value)))


    def __imul__(self, value):
        raise _BeartypeUtilCachedFixedListException(
            '{} not multipliable by {}.'.format(
                self._label, trim_object_repr(value)))

    # ..................{ BAD ~ dunders : setitem           }..................
    def __setitem__(self, index, value):

        # If these parameters indicate an external attempt to change the length
        # of this fixed length with slicing, raise an exception.
        self._die_if_slice_len_ne_value_len(index, value)

        # If this index is a tuple of 0-based indices and slice objects...
        if isinstance(index, Iterable):
            # For each index or slice in this tuple...
            for subindex in index:
                # If these parameters indicate an external attempt to change
                # the length of this fixed length with slicing, raise an
                # exception.
                self._die_if_slice_len_ne_value_len(subindex, value)

        # Else, this list is either not being sliced or is but is being set to
        # an iterable of the same length as that slice. In either case, this
        # operation preserves the length of this list and is thus acceptable.
        return super().__setitem__(index, value)


    def _die_if_slice_len_ne_value_len(self, index, value) -> None:
        '''
        Raise an exception only if the passed parameters when passed to the
        parent :meth:`__setitem__` dunder method signify an external attempt to
        change the length of this fixed length with slicing.

        This function is intended to be called by the :meth:`__setitem__`
        dunder method to validate the passed parameters.

        Parameters
        ----------
        index
            0-based index, slice object, or tuple of 0-based indices and slice
            objects to index this fixed list with.
        value
            Object to set this index(s) of this fixed list to.

        Raises
        ----------
        _BeartypeUtilCachedFixedListException
            If this index is a **slice object** (i.e., :class:`slice` instance
            underlying slice syntax) and this value is either:

            * **Unsized** (i.e., unsupported by the :func:`len` builtin).
            * Sized but has a length differing from that of this fixed list.
        '''

        # If this index is *NOT* a slice, silently reduce to a noop.
        if not isinstance(index, slice):
            return
        # Else, this index is a slice.

        # If this value is *NOT* a sized container, raise an exception.
        if not isinstance(value, Sized):
            raise _BeartypeUtilCachedFixedListException(
                '{} slice {!r} not settable to unsized {}.'.format(
                    self._label, index, trim_object_repr(value)))
        # Else, this value is a sized container.

        # 0-based first and one-past-the-last indices sliced by this slice.
        start, stop_plus_one, _ = index.indices(len(self))

        # Number of items of this fixed list sliced by this slice. By
        # definition, this is guaranteed to be a non-negative integer.
        slice_len = stop_plus_one - start

        # Number of items of this sized container to set this slice to.
        value_len = len(value)

        # If these two lengths differ, raise an exception.
        if slice_len != value_len:
            raise _BeartypeUtilCachedFixedListException(
                '{} slice {!r} of length {} not settable to '
                '{} of differing length {}.'.format(
                    self._label,
                    index,
                    slice_len,
                    trim_object_repr(value),
                    value_len,
                ))

    # ..................{ BAD ~ non-dunders                 }..................
    # Prohibit non-dunder methods modifying list length by overriding these
    # methods to raise exceptions.

    def append(self, obj):
        raise _BeartypeUtilCachedFixedListException(
            '{} not appendable by {}.'.format(
                self._label, trim_object_repr(obj)))


    def clear(self):
        raise _BeartypeUtilCachedFixedListException(
            '{} not clearable.'.format(self._label))


    def extend(self, obj):
        raise _BeartypeUtilCachedFixedListException(
            '{} not extendable by {}.'.format(
                self._label, trim_object_repr(obj)))


    def pop(self, *args):
        raise _BeartypeUtilCachedFixedListException(
            '{} not poppable.'.format(self._label))


    def remove(self, *args):
        raise _BeartypeUtilCachedFixedListException(
            '{} not removable.'.format(self._label))

    # ..................{ PRIVATE ~ property                }..................
    # Read-only properties intentionally prohibiting mutation.

    @property
    def _label(self) -> str:
        '''
        Human-readable representation of this fixed list trimmed to a
        reasonable length.

        This string property is intended to be interpolated into exception
        messages and should probably *not* be called in contexts where
        efficiency is a valid concern.
        '''

        # One-liners for magnanimous pusillanimousness.
        return 'Fixed list ' + trim_object_repr(self)
