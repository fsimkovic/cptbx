"""
Storage space for a contact map
"""

from __future__ import division

__author__ = "Felix Simkovic"
__credits__ = "Jens Thomas"
__date__ = "03 Aug 2016"
__version__ = 0.1

from conkit import constants
from conkit.core.Entity import Entity
from conkit.core.Sequence import Sequence

import collections
import numpy
import warnings

try:
    import matplotlib.pyplot
    MATPLOTLIB = True
except ImportError:
    MATPLOTLIB = False


class _Residue(object):
    """A basic class representing a residue"""
    __slots__ = ('res_seq', 'res_altseq', 'res_name', 'res_chain')

    def __init__(self, res_seq, res_altseq, res_name, res_chain):
        self.res_seq = res_seq
        self.res_altseq = res_altseq
        self.res_name = res_name
        self.res_chain = res_chain

    def __repr__(self):
        string = "Residue(res_seq='{0}' res_altseq='{1}' res_name='{2}' res_chain='{3}'"
        return string.format(self.res_seq, self.res_altseq, self.res_name, self.res_chain)


class _Gap(object):
    """A basic class representing a gap residue"""
    __slots__ = ('res_seq', 'res_altseq', 'res_name', 'res_chain')

    def __init__(self):
        self.res_seq = 9999
        self.res_altseq = 9999
        self.res_name = 'X'
        self.res_chain = ''

    def __repr__(self):
        string = "Gap(res_seq='{0}' res_altseq='{1}' res_name='{2}' res_chain='{3}'"
        return string.format(self.res_seq, self.res_altseq, self.res_name, self.res_chain)


class ContactMap(Entity):
    """A contact map object representing a single prediction

    Description
    -----------
    The :obj:`ContactMap` class represents a data structure to hold a single
    contact map prediction in one place. It contains functions to store,
    manipulate and organise :obj:`Contact` instances.

    Attributes
    ----------
    coverage : float
       The sequence coverage score
    id : str
       A unique identifier
    ncontacts : int
       The number of :obj:`Contact` instances in the :obj:`ContactMap`
    precision : float
       The precision (Positive Predictive Value) score
    repr_sequence : :obj:`Sequence`
       The representative :obj:`Sequence` associated with the :obj:`ContactMap`
    repr_sequence_altloc : :obj:`Sequence`
       The representative altloc :obj:`Sequence` associated with the :obj:`ContactMap`
    sequence : :obj:`Sequence`
       The :obj:`Sequence` associated with the :obj:`ContactMap`
    top_contact : :obj:`Contact`
       The first :obj:`Contact` entry in :obj:`ContactMap`

    Examples
    --------
    >>> from conkit.core import Contact, ContactMap
    >>> contact_map = ContactMap("example")
    >>> contact_map.add(Contact(1, 10, 0.333))
    >>> contact_map.add(Contact(5, 30, 0.667))
    >>> print(contact_map)
    ContactMap(id="example" ncontacts=2)

    """
    __slots__ = ['_sequence']

    def __init__(self, id):
        """Initialise a new contact map"""
        self._sequence = None
        super(ContactMap, self).__init__(id)

    def __repr__(self):
        return "ContactMap(id=\"{0}\", ncontacts={1})".format(self.id, self.ncontacts)

    @property
    def coverage(self):
        """The sequence coverage score

        The coverage score is calculated by analysing the number of residues
        covered by the predicted contact pairs.

        .. math::

           Coverage=\\frac{x_{cov}}{L}

        The coverage score is calculated by dividing the number of contacts
        :math:`x_{cov}` by the number of residues in the sequence :math:`L`.

        Returns
        -------
        cov : float
           The calculated coverage score

        See Also
        --------
        precision

        """
        seq_array = numpy.fromstring(self.repr_sequence.seq, dtype='uint8')
        gaps = numpy.where(seq_array == ord('-'), 1, 0)
        cov = (seq_array.size - numpy.sum(gaps, axis=0)) / seq_array.size
        return cov

    @property
    def ncontacts(self):
        """The number of :obj:`Contact` instances in the :obj:`ContactMap`

        Returns
        -------
        ncontacts : int
           The number of sequences in the :obj:`ContactMap`

        """
        return len(self)

    @property
    def precision(self):
        """The precision (Positive Predictive Value) score

        The precision value is calculated by analysing the true and false
        postive contacts.

        .. math::

           Precision=\\frac{TruePositives}{TruePositives - FalsePositives}

        The status of each contact, i.e true or false positive status, can be
        determined by running the :obj:`match()` function providing a reference
        structure.

        Returns
        -------
        ppv : float
           The calculated precision score

        See Also
        --------
        coverage

        """
        status_array = numpy.asarray([c.status for c in self])

        fp_count = numpy.sum(numpy.where(status_array == -1, 1, 0))
        uk_count = numpy.sum(numpy.where(status_array == 0, 1, 0))
        tp_count = numpy.sum(numpy.where(status_array == 1, 1, 0))

        if fp_count == 0.0 and tp_count == 0.0:
            warnings.warn('Contact status unknown. Match two contact maps first!')
            return 0.0
        elif uk_count > 0:
            warnings.warn('Some contacts in your map are unmatched - Precision value might be inaccurate')

        return tp_count / (tp_count + fp_count)

    @property
    def repr_sequence(self):
        """The representative :obj:`Sequence` associated with the :obj:`ContactMap`

        The peptide sequence constructed from the available
        contacts using the normal res_seq positions

        Returns
        -------
        sequence : :obj:`Sequence`

        Raises
        ------
        TypeError
           Sequence undefined

        See Also
        --------
        repr_sequence_altloc, sequence

        """
        if not isinstance(self.sequence, Sequence):
            raise TypeError('Define the sequence as Sequence() instance')
        # Get all resseqs that are the contact map
        res1_seqs, res2_seqs = zip(*[contact.id for contact in self])
        res_seqs = set(
            sorted(res1_seqs + res2_seqs)
        )
        return self._construct_repr_sequence(list(res_seqs))

    @property
    def repr_sequence_altloc(self):
        """The representative altloc :obj:`Sequence` associated with the :obj:`ContactMap`

        The peptide sequence constructed from the available
        contacts using the altloc res_seq positions

        Returns
        -------
        sequence : :obj:`Sequence`

        Raises
        ------
        ValueError
           Sequence undefined

        See Also
        --------
        repr_sequence, sequence

        """
        if not isinstance(self.sequence, Sequence):
            raise TypeError('Define the sequence as Sequence() instance')
        # Get all resseqs that are the contact map
        res1_seqs, res2_seqs = zip(*[(contact.res1_altseq, contact.res2_altseq) for contact in self])
        res_seqs = set(
            sorted(res1_seqs + res2_seqs)
        )
        return self._construct_repr_sequence(list(res_seqs))

    @property
    def sequence(self):
        """The :obj:`Sequence` associated with the :obj:`ContactMap`

        Returns
        -------
        :obj:`Sequence`

        See Also
        --------
        repr_sequence, repr_sequence_altloc

        """
        return self._sequence

    @sequence.setter
    def sequence(self, sequence):
        """Associate a :obj:`Sequence` instance with the :obj:`ContactMap`

        Parameters
        ----------
        sequence : :obj:`Sequence`

        Raises
        ------
        ValueError
           Incorrect hierarchy instance provided

        """
        if not isinstance(sequence, Sequence):
            raise TypeError('Instance of Sequence() required: {0}'.format(sequence))
        self._sequence = sequence

    @property
    def top_contact(self):
        """The first :obj:`Contact` entry in :obj:`ContactMap`

        Returns
        -------
        top_contact : :obj:`Contact`, None
           The first :obj:`Contact` entry in :obj:`ContactFile`

        """
        if len(self) > 0:
            return self[0]
        else:
            return None

    def _construct_repr_sequence(self, res_seqs):
        """Construct the representative sequence"""
        # Determine which are present and which are not
        representative_sequence = ''
        for i in xrange(1, self.sequence.seq_len + 1):
            if i in res_seqs:
                representative_sequence += self.sequence.seq[i - 1]
            else:
                representative_sequence += '-'
        return Sequence(self.sequence.id + '_repr', representative_sequence)

    def assign_sequence_register(self, altloc=False):
        """Assign the amino acids from :obj:`Sequence` to all :obj:`Contact` instances

        Parameters
        ----------
        altloc : bool
           Use the res_altloc positions [default: False]

        """
        for c in self:
            if altloc:
                res1_index, res2_index = c.res1_altseq, c.res2_altseq
            else:
                res1_index, res2_index = c.res1_seq, c.res2_seq
            c.res1 = self.sequence.seq[res1_index - 1]
            c.res2 = self.sequence.seq[res2_index - 1]

    def calculate_scalar_score(self):
        """Calculate a scaled score for the :obj:`ContactMap`

        This score is a scaled score for all raw scores in a contact
        map. It is defined by the formula

        .. math::

           {x}'=\\frac{x}{\\overline{d}}

        where :math:`x` corresponds to the raw score of each predicted
        contact and :math:`\overline{d}` to the mean of all raw scores.

        The score is saved in a separate :obj:`Contact` attribute called
        ``scalar_score``

        This score is described in more detail in Ovchinnikov et al. (2015).

        """
        raw_scores = numpy.asarray([c.raw_score for c in self])
        sca_scores = raw_scores / numpy.mean(raw_scores)
        for contact, sca_score in zip(self, sca_scores):
            contact.scalar_score = sca_score
        return

    def create_keymap(self, altloc=False):
        """Create a simple keymap

        Paramters
        ---------
        altloc : bool
           Use the res_altloc positions [default: False]

        """
        contact_map_keymap = collections.OrderedDict()

        for contact in self:
            pos1 = _Residue(contact.res1_seq, contact.res1_altseq, contact.res1, contact.res1_chain)
            pos2 = _Residue(contact.res2_seq, contact.res2_altseq, contact.res2, contact.res2_chain)

            if altloc:
                res1_index, res2_index = contact.res1_altseq, contact.res2_altseq
            else:
                res1_index, res2_index = contact.res1_seq, contact.res2_seq

            contact_map_keymap[res1_index] = pos1
            contact_map_keymap[res2_index] = pos2

        contact_map_keymap_sorted = sorted(contact_map_keymap.items(), key=lambda x: int(x[0]))
        return zip(*contact_map_keymap_sorted)[1]

    def find(self, indexes, altloc=False):
        """Find all contacts associated with ``index``

        Parameters
        ----------
        index : list, tuple
           A list of residue indexes to find
        altloc : bool
           Use the res_altloc positions [default: False]

        Returns
        -------
        :obj:`ContactMap`
           A modified version of the contact map containing
           the found contacts

        See Also
        --------
        find_gen

        """
        contact_map = self.copy()
        for contact in self:
            if altloc and (contact.res1_altseq in indexes or contact.res2_altseq in indexes):
                continue
            elif contact.res1_seq in indexes or contact.res2_seq in indexes:
                continue
            else:
                contact_map.remove(contact.id)
        return contact_map

    def find_gen(self, indexes, altloc=False):
        """Find all contacts associated with ``index``

        Parameters
        ----------
        index : list, tuple
           A list of residue indexes to find
        altloc : bool
           Use the res_altloc positions [default: False]

        Yields
        ------
        generator
           A generator containing contacts

        Notes
        -----
        Unlike :obj:`find()`, this function returns a generator without
        the :obj:`ContactMap` wrapper. It is therefore much faster to access
        but less suitable for further handling

        See Also
        --------
        find

        """
        for contact in self:
            if altloc and (contact.res1_altseq in indexes or contact.res2_altseq in indexes):
                yield contact
            elif contact.res1_seq in indexes or contact.res2_seq in indexes:
                yield contact

    def match(self, other, remove_unmatched=False, renumber=False, inplace=False):
        """Modify both hierarchies so residue numbers match one another.

        This function is key when plotting contact maps or visualising
        contact maps in 3-dimensional space. In particular, when residue
        numbers in the structure do not start at count 0 or when peptide
        chain breaks are present.

        Parameters
        ----------
        other : :obj:`ContactMap`
           A ConKit :obj:`ContactMap`
        remove_unmatched : bool, optional
           Remove all unmatched contacts [default: False]
        renumber : bool, optional
           Renumber the res_seq entries [default: False]

           If ``True``, ``res1_seq`` and ``res2_seq`` changes
           but ``id`` remains the same
        inplace : bool, optional
           Replace the saved order of contacts [default: False]

        Returns
        -------
        hierarchy_mod, hierarchy_ref
           Two ConKit :obj:`ContactMap` instances, regardless of inplace

        """
        contact_map1 = self._inplace(inplace)
        contact_map2 = other._inplace(inplace)

        # ================================================================
        # 1. Align all sequences
        # ================================================================

        # Align both full sequences against each other
        aligned_sequences_full = contact_map1.sequence.align_local(contact_map2.sequence, id_chars=2,
                                                                   nonid_chars=1, gap_open_pen=-0.5,
                                                                   gap_ext_pen=-0.1)
        contact_map1_full_sequence, contact_map2_full_sequence = aligned_sequences_full

        # Align contact map 1 full sequences with representative sequence
        aligned_sequences_map1 = contact_map1_full_sequence.align_local(contact_map1.repr_sequence,
                                                                        id_chars=2, nonid_chars=1, gap_open_pen=-0.5,
                                                                        gap_ext_pen=-0.2, inplace=True)
        contact_map1_repr_sequence = aligned_sequences_map1[-1]

        # Align contact map 2 full sequences with __ALTLOC__ representative sequence
        aligned_sequences_map2 = contact_map2_full_sequence.align_local(contact_map2.repr_sequence_altloc,
                                                                        id_chars=2, nonid_chars=1, gap_open_pen=-0.5,
                                                                        gap_ext_pen=-0.2, inplace=True)
        contact_map2_repr_sequence = aligned_sequences_map2[-1]

        # Align both aligned representative sequences
        aligned_sequences_repr = contact_map1_repr_sequence.align_local(contact_map2_repr_sequence,
                                                                        id_chars=2, nonid_chars=1, gap_open_pen=-1.0,
                                                                        gap_ext_pen=-0.5, inplace=True)
        contact_map1_repr_sequence, contact_map2_repr_sequence = aligned_sequences_repr

        # ================================================================
        # 2. Identify TPs in other, map them, and match them to self
        # ================================================================

        # Encode the sequences to uint8 character arrays for easier and faster handling
        encoded_repr = numpy.asarray([
            numpy.fromstring(contact_map1_repr_sequence.seq, dtype='uint8'),
            numpy.fromstring(contact_map2_repr_sequence.seq, dtype='uint8')
        ])

        # Create mappings for both contact maps
        contact_map1_keymap = contact_map1.create_keymap()
        contact_map2_keymap = contact_map2.create_keymap(altloc=True)

        # Some checks
        assert len(contact_map1_keymap) == len(numpy.where(encoded_repr[0] != ord('-'))[0])
        assert len(contact_map2_keymap) == len(numpy.where(encoded_repr[1] != ord('-'))[0])

        # Create a sequence matching keymap including deletions and insertions
        keymaps = [[], []]
        it_contact_map1 = iter(contact_map1_keymap)
        it_contact_map2 = iter(contact_map2_keymap)
        for amino_acid1, amino_acid2 in zip(encoded_repr[0], encoded_repr[1]):
            if amino_acid1 == ord('-'):
                keymaps[0].append(_Gap())
            else:
                keymaps[0].append(it_contact_map1.next())

            if amino_acid2 == ord('-'):
                keymaps[1].append(_Gap())
            else:
                keymaps[1].append(it_contact_map2.next())
        contact_map1_keymap, contact_map2_keymap = keymaps

        # Reindex the altseq positions to account for insertions/deletions
        def reindex(keymap):
            """Reindex a key map"""
            for i, residue in enumerate(keymap):
                if isinstance(residue, _Residue):
                    residue.res_altseq = i + 1
            return keymap
        contact_map1_keymap = reindex(contact_map1_keymap)
        contact_map2_keymap = reindex(contact_map2_keymap)

        # TODO: Find a speed-up for this loop
        # Adjust contact_map2 altseqs based on the insertions and deletions
        encoder = dict((x.res_seq, x.res_altseq) for x in contact_map2_keymap if isinstance(x, _Residue))
        for contact in contact_map2:
            if contact.res1_altseq in encoder.keys():
                contact.res1_altseq = encoder[contact.res1_altseq]
            if contact.res2_altseq in encoder.keys():
                contact.res2_altseq = encoder[contact.res2_altseq]
            # Adjust true and false positive statuses
            id = (contact.res1_altseq, contact.res2_altseq)
            if id in contact_map1:
                contact_map1[id].status = contact.status

        # ================================================================
        # 3. Remove unmatched contacts
        # ================================================================
        if remove_unmatched:
            for residue1, residue2 in zip(contact_map1_keymap, contact_map2_keymap):
                if isinstance(residue1, _Gap):
                    continue
                elif isinstance(residue2, _Gap):
                    for contact in contact_map1.find([residue1.res_seq]):
                        contact_map1.remove(contact.id)

        # ================================================================
        # 4. Renumber the contact map 1 based on contact map 2
        # ================================================================
        if renumber:
            for residue1, residue2 in zip(contact_map1_keymap, contact_map2_keymap):
                if isinstance(residue1, _Gap):
                    continue
                for contact in contact_map1.find_gen([residue1.res_seq]):
                    if contact.res1_seq == residue1.res_seq:
                        contact.res1_seq = residue2.res_seq
                        contact.res1_chain = residue2.res_chain
                    else:
                        contact.res2_seq = residue2.res_seq
                        contact.res2_chain = residue2.res_chain

        return contact_map1, contact_map2

    def remove_neighbors(self, min_distance=5, inplace=False):
        """Remove contacts between neighboring residues

        Parameters
        ----------
        min_distance : int, optional
           The minimum number of residues between contacts  [default: 5]
        inplace : bool, optional
           Replace the saved order of contacts [default: False]

        Returns
        -------
        contact_map : :obj:`ContactMap`
           The reference to the :obj:`ContactMap`, regardless of inplace

        """
        contact_map = self._inplace(inplace)

        for contact in reversed(contact_map):
            if abs(contact.res1_seq - contact.res2_seq) < min_distance:
                contact_map.remove(contact.id)

        return contact_map

    def plot_map(self, other=None, reference=None, altloc=False, file_format='png', file_name='contactmap.png'):
        """Produce a 2D contact map plot

        Parameters
        ----------
        other : :obj:`ContactMap`, optional
           A ConKit :obj:`ContactMap`
        reference : :obj:`ContactMap`, optional
           A ConKit :obj:`ContactMap` [this map refers to the reference contacts]
        altloc : bool
           Use the res_altloc positions [default: False]
        file_format : str, optional
           Plot figure format. See matplotlib :obj:`savefig()` for options  [default: png]
        file_name : str, optional
           File name to which the contact map will be printed  [default: contactmap.png]

        Warnings
        --------
        If the ``file_name`` variable is not changed, the current file will be
        continuously overwritten.

        Raises
        ------
        RuntimeError
           Matplotlib not installed

        """
        if not MATPLOTLIB:
            raise RuntimeError('Dependency not found: matplotlib')

        fig, ax = matplotlib.pyplot.subplots(figsize=(5, 5), dpi=600)

        # Plot the other_ref contacts
        if reference:
            if altloc:
                reference_data = numpy.asarray([(c.res1_altseq, c.res2_altseq)
                                                for c in reference if c.is_true_positive])
            else:
                reference_data = numpy.asarray([(c.res1_seq, c.res2_seq)
                                                for c in reference if c.is_true_positive])
            reference_colors = [constants.RFCOLOR for _ in xrange(len(reference_data))]
            ax.scatter(reference_data.T[0], reference_data.T[1], color=reference_colors,
                       marker='.', s=10, edgecolor='none', linewidths=0.0)
            ax.scatter(reference_data.T[1], reference_data.T[0], color=reference_colors,
                       marker='.', s=10, edgecolor='none', linewidths=0.0)

        # Plot the self contacts
        self_data = numpy.asarray([(c.res1_seq, c.res2_seq) for c in self])
        self_colors = [
            constants.TPCOLOR if contact.is_true_positive
            else constants.FPCOLOR if contact.is_false_positive
            else constants.NTCOLOR for contact in self
        ]
        # This is the bottom triangle
        ax.scatter(self_data.T[1], self_data.T[0], color=self_colors,
                   marker='.', s=10, edgecolor='none', linewidths=0.0)

        # Plot the other contacts
        if other:
            other_data = numpy.asarray([(c.res1_seq, c.res2_seq) for c in other])
            other_colors = [
                constants.TPCOLOR if contact.is_true_positive
                else constants.FPCOLOR if contact.is_false_positive
                else constants.NTCOLOR for contact in other
            ]
            # This is the upper triangle
            ax.scatter(other_data.T[0], other_data.T[1], color=other_colors,
                    marker='.', s=10, edgecolor='none', linewidths=0.0)
        else:
            # This is the upper triangle
            ax.scatter(self_data.T[0], self_data.T[1], color=self_colors,
                               marker='.', s=10, edgecolor='none', linewidths=0.0)

        # Prettify the plot
        label = 'Residue number'
        ax.set_xlabel(label)
        ax.set_ylabel(label)

        # Allow dynamic x and y limits
        min_res_seq = numpy.min(self_data.ravel()) - 5
        max_res_seq = numpy.max(self_data.ravel()) + 5
        if other:
            min_res_seq = numpy.min(numpy.append(self_data.ravel(), other_data.ravel())) - 5
            max_res_seq = numpy.max(numpy.append(self_data.ravel(), other_data.ravel())) + 5
        ax.set_xlim(min_res_seq, max_res_seq)
        ax.set_ylim(min_res_seq, max_res_seq)

        # fig.tight_layout()

        _, file_extension = file_name.rsplit('.', 1)
        if file_extension != file_format:
            raise ValueError('File extension and file format have to be identical: '
                             '{0} - {1} are not'.format(file_extension, file_format))
        fig.savefig(file_name, format=file_format.lower())

    def rescale(self, inplace=False):
        """Rescale the raw scores in :obj:`ContactMap`

        Rescaling of the data is done to normalize the raw scores
        to be in the range [0, 1]. The formula to rescale the data is:

        .. math::

           {x}'=\\frac{x-min(d)}{max(d)-min(d)}

        :math:`x` is the original value and :math:`d` are all values to be
        rescaled.

        Parameters
        ----------
        inplace : bool, optional
           Replace the saved order of contacts [default: False]

        Returns
        -------
        contact_map : :obj:`ContactMap`
           The reference to the :obj:`ContactMap`, regardless of inplace

        """
        contact_map = self._inplace(inplace)

        raw_scores = numpy.asarray([c.raw_score for c in contact_map])
        norm_raw_scores = (raw_scores - raw_scores.min()) / (raw_scores.max() - raw_scores.min())

        for contact, norm_raw_score in zip(contact_map, norm_raw_scores):
            contact.raw_score = norm_raw_score

        return contact_map

    def sort(self, kword, reverse=False, inplace=False):
        """Sort the :obj:`ContactMap`

        Parameters
        ----------
        kword : str
           The dictionary key to sort contacts by
        reverse : bool, optional
           Sort the contact pairs in descending order [default: False]
        inplace : bool, optional
           Replace the saved order of contacts [default: False]

        Returns
        -------
        contact_map : :obj:`ContactMap`
           The reference to the :obj:`ContactMap`, regardless of inplace

        Raises
        ------
        ValueError
           ``kword`` not in :obj:`ContactMap`

        """
        contact_map = self._inplace(inplace)
        contact_map._sort(kword, reverse)
        return contact_map
