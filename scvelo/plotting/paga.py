from .. import settings
from .. import logging as logg

from ..tools.utils import groups_to_bool
from .utils import default_basis, default_size, savefig_or_show, \
    default_color, make_unique_list, make_unique_valid_list, get_components
from .scatter import scatter
from .docs import doc_scatter, doc_params

from matplotlib import rcParams
import matplotlib.pyplot as pl
import numpy as np
from inspect import signature
import collections.abc as cabc


@doc_params(scatter=doc_scatter)
def paga(adata, basis=None, vkey='velocity', color=None, layer=None, title=None, threshold=None, layout=None,
         layout_kwds={}, init_pos=None, root=0, labels=None, single_component=False, dashed_edges='connectivities',
         solid_edges='transitions_confidence', transitions='transitions_confidence', node_size_scale=1, node_size_power=0.5,
         edge_width_scale=.4, min_edge_width=None, max_edge_width=2, arrowsize=15, random_state=0, pos=None,
         node_colors=None, normalize_to_color=False, cmap=None, cax=None, cb_kwds={}, add_pos=True,
         export_to_gexf=False, plot=True, use_raw=None, size=None, groups=None, components=None, figsize=None, dpi=None,
         show=True, save=None, ax=None, ncols=None, scatter_flag=None, **kwargs):
    """\
    Plot directed PAGA transition tree.

    PAGA graph with connectivities (dashed) and transitions (solid/arrows).

    Parameters
    ----------
    adata
        Annotated data matrix.
    threshold
        Do not draw edges for weights below this threshold. Set to 0 if you want
        all edges. Discarding low-connectivity edges helps in getting a much
        clearer picture of the graph.
    color
        Gene name or `obs` annotation defining the node colors.
        Also plots the degree of the abstracted graph when
        passing 'degree_dashed' or 'degree_solid'.
    labels
        The node labels. If `None`, this defaults to the group labels stored in
        the categorical for which :func:`~scanpy.tl.paga` has been computed.
    pos
        Two-column array-like storing the x and y coordinates for drawing.
        Otherwise, path to a `.gdf` file that has been exported from Gephi or
        a similar graph visualization software.
    layout
        Plotting layout that computes positions.
        `'fa'` stands for ForceAtlas2,
        `'fr'` stands for Fruchterman-Reingold,
        `'rt'` stands for Reingold-Tilford,
        `'eq_tree'` stands for eqally spaced tree.
        All but `'fa'` and `'eq_tree'` are igraph layouts.
        All other igraph layouts are also permitted.
    layout_kwds
        Keywords for the layout.
    init_pos
        Two-column array storing the x and y coordinates for initializing the layout.
    random_state
        For layouts with random initialization like `'fr'`, change this to use
        different intial states for the optimization. If `None`, the initial
        state is not reproducible.
    root
        If choosing a tree layout, this is the index of the root node or a list
        of root node indices. If this is a non-empty vector then the supplied
        node IDs are used as the roots of the trees (or a single tree if the
        graph is connected). If this is `None` or an empty list, the root
        vertices are automatically calculated based on topological sorting.
    transitions
        Key for `.uns['paga']` that specifies the matrix that – for instance
        `'transistions_confidence'` – that specifies the matrix that stores the
        arrows.
    solid_edges
        Key for `.uns['paga']` that specifies the matrix that stores the edges
        to be drawn solid black.
    dashed_edges
        Key for `.uns['paga']` that specifies the matrix that stores the edges
        to be drawn dashed grey. If `None`, no dashed edges are drawn.
    single_component
        Restrict to largest connected component.
    fontsize
        Font size for node labels.
    fontoutline
        Width of the white outline around fonts.
    text_kwds
        Keywords for :meth:`~matplotlib.axes.Axes.text`.
    node_size_scale
        Increase or decrease the size of the nodes.
    node_size_power
        The power with which groups sizes influence the radius of the nodes.
    edge_width_scale
        Edge with scale in units of `rcParams['lines.linewidth']`.
    min_edge_width
        Min width of solid edges.
    max_edge_width
        Max width of solid and dashed edges.
    arrowsize
       For directed graphs, choose the size of the arrow head head's length and
       width. See :py:class: `matplotlib.patches.FancyArrowPatch` for attribute
       `mutation_scale` for more info.
    export_to_gexf
        Export to gexf format to be read by graph visualization programs such as
        Gephi.
    normalize_to_color
        Whether to normalize categorical plots to `color` or the underlying
        grouping.
    cmap
        The color map.
    cax
        A matplotlib axes object for a potential colorbar.
    cb_kwds
        Keyword arguments for :class:`~matplotlib.colorbar.ColorbarBase`, for instance, `ticks`.
    add_pos
        Add the positions to `adata.uns['paga']`.
    title
        Provide a title.
    frameon
        Draw a frame around the PAGA graph.
    plot
        If `False`, do not create the figure, simply compute the layout.
    save
        If `True` or a `str`, save the figure. A string is appended to the default filename.
        Infer the filetype if ending on '.pdf', '.png', or '.svg'.
    ax
        A matplotlib axes object.

    {scatter}

    Returns
    -------
    If `show==False`, one or more :class:`~matplotlib.axes.Axes` objects.
    Adds `'pos'` to `adata.uns['paga']` if `add_pos` is `True`.
    """

    if scatter_flag is None:
        scatter_flag = ax is None
    vkey = [key for key in adata.layers.keys() if 'velocity' in key and '_u' not in key] if vkey == 'all' else vkey
    layers, vkeys, colors = make_unique_list(layer), make_unique_list(vkey), make_unique_list(color, allow_array=True)

    node_colors = colors if node_colors is None else node_colors
    bases = [default_basis(adata) if basis is None else basis for basis in make_unique_valid_list(adata, basis)]
    if transitions not in adata.uns['paga']: transitions = None
    if min_edge_width is not None: max_edge_width = max(min_edge_width, max_edge_width)

    if threshold is None and 'threshold' in adata.uns['paga']: threshold = adata.uns['paga']['threshold']
    paga_kwargs = {'threshold': threshold, 'layout': layout, 'layout_kwds': layout_kwds, 'init_pos': init_pos,
                   'root': root, 'labels': labels, 'single_component': single_component,
                   'solid_edges': solid_edges, 'dashed_edges': dashed_edges, 'transitions': transitions,
                   'node_size_scale': node_size_scale, 'node_size_power': node_size_power,
                   'edge_width_scale': edge_width_scale, 'min_edge_width': min_edge_width,
                   'max_edge_width': max_edge_width, 'arrowsize': arrowsize, 'random_state': random_state,
                   'pos': pos, 'normalize_to_color': normalize_to_color, 'cmap': cmap, 'cax': cax, 'cb_kwds': cb_kwds,
                   'add_pos': add_pos, 'export_to_gexf': export_to_gexf, 'colors': node_colors, 'plot': plot}

    for key in kwargs:
        if key in signature(_paga).parameters:
            paga_kwargs[key] = kwargs[key]
    kwargs = {k: v for k, v in kwargs.items() if k in signature(scatter).parameters}

    if isinstance(node_colors, dict):  # has to be disabled
        paga_kwargs['colorbar'] = False

    multikey = colors if len(colors) > 1 else layers if len(layers) > 1 \
        else vkeys if len(vkeys) > 1 else bases if len(bases) > 1 else None
    if multikey is not None:
        if title is None:
            title = list(multikey)
        elif isinstance(title, (list, tuple)):
            title *= int(np.ceil(len(multikey) / len(title)))
        ncols = len(multikey) if ncols is None else min(len(multikey), ncols)
        nrows = int(np.ceil(len(multikey) / ncols))
        figsize = rcParams['figure.figsize'] if figsize is None else figsize
        ax = []
        for i, gs in enumerate(
                pl.GridSpec(nrows, ncols, pl.figure(None, (figsize[0] * ncols, figsize[1] * nrows), dpi=dpi))):
            if i < len(multikey):
                ax.append(paga(adata, size=size, ax=pl.subplot(gs), scatter_flag=scatter_flag,
                               basis=bases[i] if len(bases) > 1 else basis,
                               color=colors[i] if len(colors) > 1 else color,
                               layer=layers[i] if len(layers) > 1 else layer,
                               vkey=vkeys[i] if len(vkeys) > 1 else vkey,
                               title=title[i] if isinstance(title, (list, tuple)) else title,
                               **kwargs, **paga_kwargs))
        savefig_or_show(dpi=dpi, save=save, show=show)
        if not show: return ax

    else:

        color, layer, vkey, basis = colors[0], layers[0], vkeys[0], basis
        color = default_color(adata) if color is None else color
        size = default_size(adata) / 2 if size is None else size

        paga_groups = adata.uns['paga']['groups']
        _adata = adata[groups_to_bool(adata, groups, groupby=paga_groups)] \
            if groups is not None and paga_groups in adata.obs.keys() else adata

        if isinstance(node_colors, str) and node_colors in adata.obsm.keys():
            props = dict()
            for name in adata.obs[paga_groups].cat.categories:
                mask = (adata.obs[paga_groups] == name).values
                props[name] = np.nanmean(adata.obsm[node_colors][mask], axis=0)
            node_colors = adata.obsm[node_colors].colors
            paga_kwargs['colors'] = {i: dict(zip(node_colors, prop)) for i, prop in enumerate(props.values())}
            paga_kwargs['colorbar'] = False

        if basis in adata.var_names and basis is not None:
            x = adata[:, basis].layers['spliced'] if use_raw else adata[:, basis].layers['Ms']
            y = adata[:, basis].layers['unspliced'] if use_raw else adata[:, basis].layers['Mu']
        elif basis is not None:
            X_emb = adata.obsm['X_' + basis][:, get_components(components, basis)]
            x, y = X_emb[:, 0], X_emb[:, 1]

        if basis is None and pos is None:
            pos = None  # default to paga embedding
        elif pos is None:
            if 'paga' in adata.uns:
                # Recompute the centroid positions
                categories = list(adata.obs[paga_groups].cat.categories)
                pos = np.zeros((len(categories), 2))
                for ilabel, label in enumerate(categories):
                    X_emb = adata.obsm['X_' + basis][adata.obs[paga_groups] == label, :2]
                    x_pos, y_pos = np.median(X_emb, axis=0)
                    pos[ilabel] = [x_pos, y_pos]
            else:
                raise ValueError(
                    'You need to run `scv.tl.paga` first.')
        paga_kwargs['pos'] = pos

        legend_loc = kwargs.pop('legend_loc', 'right')
        if legend_loc is None: legend_loc = 'none'
        kwargs['legend_loc'] = 'none' if legend_loc == 'on data' else legend_loc  # let paga handle 'on data'
        if 'frameon' not in paga_kwargs or not paga_kwargs['frameon']:
            paga_kwargs['frameon'] = False
        kwargs['frameon'] = paga_kwargs['frameon']
        if title is None:
            title = f'paga ({str(paga_groups)})' if transitions is None else f'paga velocity-graph ({str(paga_groups)})'

        ax = pl.figure(None, figsize, dpi=dpi).gca() if ax is None else ax
        if scatter_flag and basis is not None:
            if 'alpha' not in kwargs: kwargs['alpha'] = .5
            ax = scatter(adata, basis=basis, x=x, y=y, vkey=vkey, layer=layer, color=paga_groups, size=size,
                         title=title, ax=ax, save=None, zorder=0, show=False, **kwargs)

        _paga(adata, ax=ax, show=False,  **paga_kwargs, text_kwds={'zorder': 1000, 'alpha': legend_loc == 'on data'})

        savefig_or_show(dpi=dpi, save=save, show=show)
        if not show: return ax


def _paga(adata, threshold=None, color=None, layout=None, layout_kwds=None, init_pos=None, root=0,
                labels=None, single_component=False, solid_edges='connectivities', dashed_edges=None,
                transitions=None, fontsize=None, fontweight='bold', fontoutline=None, text_kwds=None,
                node_size_scale=1, node_size_power=0.5, edge_width_scale=1, min_edge_width=None, max_edge_width=None,
                arrowsize=30, title=None, random_state=0, pos=None, normalize_to_color=False, cmap=None, cax=None,
                colorbar=None, cb_kwds=None, frameon=None, add_pos=True, export_to_gexf=False, use_raw=True,
                colors=None, groups=None, plot=True, show=None, save=None, ax=None, **scatter_kwargs):
    """scanpy/_paga with some adjustments for directional graphs. To be moved back to scanpy once finalized.
    """
    from scanpy.plotting._tools.paga import _compute_pos, _utils
    if groups is not None: labels = groups
    if colors is None: colors = color
    groups_key = adata.uns['paga']['groups']

    def is_flat(x):
        has_one_per_category = (isinstance(x, cabc.Collection) and len(x) == len(adata.obs[groups_key].cat.categories))
        return has_one_per_category or x is None or isinstance(x, str)

    if is_flat(colors):
        colors = [colors]
    if is_flat(labels):
        labels = [labels for _ in range(len(colors))]
    title = [c for c in colors] if title is None and len(colors) > 1 \
        else [title for _ in colors] if isinstance(title, str) \
        else [None for _ in colors] if title is None else title

    if colorbar is None:
        colorbars = [((c in adata.obs_keys() and adata.obs[c].dtype.name != 'category') or
                      (c in adata.var_names if adata.raw is None else adata.raw.var_names)) for c in colors]
    else:
        colorbars = [False for _ in colors]

    if isinstance(root, str):
        if root not in labels:
            raise ValueError(f'If `root` is a string, it needs to be one of {labels} not {root!r}.')
        root = list(labels).index(root)
    if isinstance(root, cabc.Sequence) and root[0] in labels:
        root = [list(labels).index(r) for r in root]

    # define the adjacency matrices
    if solid_edges not in adata.uns['paga']:
        logg.warn(f'{solid_edges} not found, using connectivites instead.')
        solid_edges = 'connectivities'
    adjacency_solid = adata.uns['paga'][solid_edges].copy()
    adjacency_dashed = None
    if threshold is None:
        threshold = 0.01  # default threshold
    if threshold > 0:
        adjacency_solid.data[adjacency_solid.data < threshold] = 0
        adjacency_solid.eliminate_zeros()
    if dashed_edges is not None:
        adjacency_dashed = adata.uns['paga'][dashed_edges].copy()
        if threshold > 0:
            adjacency_dashed.data[adjacency_dashed.data < threshold] = 0
            adjacency_dashed.eliminate_zeros()

    cats = adata.obs[groups_key].cat.categories
    if pos is not None:
        if isinstance(pos, str):
            if not pos.startswith('X_'): pos = 'X_' + pos
            pos = np.stack([np.median(adata.obsm[pos][adata.obs[groups_key] == c], axis=0) for c in cats]) \
                if pos in adata.obsm.keys() else None
        if len(pos) != len(cats):
            pos = None
    elif init_pos is not None:
        if isinstance(init_pos, str):
            if not init_pos.startswith('X_'): init_pos = 'X_' + init_pos
            init_pos = np.stack([np.median(adata.obsm[init_pos][adata.obs[groups_key] == c], axis=0) for c in cats]) \
                if init_pos in adata.obsm.keys() else None
        if len(init_pos) != len(cats):
            init_pos = None

    # compute positions
    if pos is None:
        adj_tree = None
        if layout in {'rt', 'rt_circular', 'eq_tree'}:
            adj_tree = adata.uns['paga']['connectivities_tree']
        pos = _compute_pos(adjacency_solid, layout=layout, random_state=random_state, init_pos=init_pos,
                           layout_kwds=layout_kwds, adj_tree=adj_tree, root=root)
        #pos = adata.uns['paga']['pos']

    scatter_kwargs.update({'alpha': 0, 'color': groups_key})
    x, y = pos[:, 0], pos[:, 1]

    if plot:
        axs, panel_pos, draw_region_width, figure_width = _utils.setup_axes(ax=ax, panels=colors, colorbars=colorbars)

        if len(colors) == 1 and not isinstance(axs, list):
            axs = [axs]

        for icolor, c in enumerate(colors):
            if title[icolor] is not None:
                axs[icolor].set_title(title[icolor])
            axs[icolor] = scatter(adata, x=x, y=y, title=title[icolor], ax=axs[icolor], save=None, zorder=0, show=False, **scatter_kwargs)
            sct = _paga_graph(adata, axs[icolor], colors=c, solid_edges=solid_edges, dashed_edges=dashed_edges,
                              transitions=transitions, threshold=threshold, adjacency_solid=adjacency_solid,
                              adjacency_dashed=adjacency_dashed, root=root, labels=labels[icolor], fontsize=fontsize,
                              fontweight=fontweight, fontoutline=fontoutline, text_kwds=text_kwds,
                              node_size_scale=node_size_scale, node_size_power=node_size_power,
                              edge_width_scale=edge_width_scale, min_edge_width=min_edge_width,
                              max_edge_width=max_edge_width, normalize_to_color=normalize_to_color, frameon=frameon,
                              cmap=cmap, colorbar=colorbars[icolor], cb_kwds=cb_kwds, use_raw=use_raw,
                              title=title[icolor], export_to_gexf=export_to_gexf, single_component=single_component,
                              arrowsize=arrowsize, pos=pos)
            if colorbars[icolor]:
                if cax is None:
                    bottom = panel_pos[0][0]
                    height = panel_pos[1][0] - bottom
                    width = 0.006 * draw_region_width / len(colors)
                    left = panel_pos[2][2*icolor+1] + 0.2 * width
                    rectangle = [left, bottom, width, height]
                    fig = pl.gcf()
                    ax_cb = fig.add_axes(rectangle)
                else:
                    ax_cb = cax[icolor]

                cb = pl.colorbar(sct, cax=ax_cb)
    if add_pos:
        adata.uns['paga']['pos'] = pos
    if plot:
        savefig_or_show('paga', show=show, save=save)
        if len(colors) == 1 and isinstance(axs, list): axs = axs[0]
        if show is False:
            return axs


def _paga_graph(adata, ax, solid_edges=None, dashed_edges=None, adjacency_solid=None, adjacency_dashed=None,
                transitions=None, threshold=None, root=0, colors=None, labels=None, fontsize=None, fontweight=None,
                fontoutline=None, text_kwds=None, node_size_scale=1., node_size_power=0.5, edge_width_scale=1.,
                normalize_to_color='reference', title=None, pos=None, cmap=None, frameon=True, min_edge_width=None,
                max_edge_width=None, export_to_gexf=False, colorbar=None, use_raw=True, cb_kwds=None,
                single_component=False, arrowsize=30):
    """scanpy/_paga_graph with some adjustments for directional graphs. To be moved back to scanpy once finalized.
    """
    import networkx as nx
    import pandas as pd
    import scipy
    import warnings
    from matplotlib import patheffects
    from matplotlib.colors import is_color_like
    from pathlib import Path
    from scanpy.plotting._tools.paga import _utils
    from pandas.api.types import is_categorical_dtype

    node_labels = labels  # rename for clarity
    if node_labels is not None and isinstance(node_labels, str) and node_labels != adata.uns['paga']['groups']:
        raise ValueError('Provide a list of group labels for the PAGA groups {}, not {}.'
                         .format(adata.uns['paga']['groups'], node_labels))
    groups_key = adata.uns['paga']['groups']
    if node_labels is None:
        node_labels = adata.obs[groups_key].cat.categories

    if (colors is None or colors == groups_key) and groups_key is not None:
        if groups_key + '_colors' not in adata.uns \
                or len(adata.obs[groups_key].cat.categories) != len(adata.uns[groups_key + '_colors']):
            _utils.add_colors_for_categorical_sample_annotation(adata, groups_key)
        colors = adata.uns[groups_key + '_colors']

    nx_g_solid = nx.Graph(adjacency_solid)
    if dashed_edges is not None:
        nx_g_dashed = nx.Graph(adjacency_dashed)

    # convert pos to array and dict
    if not isinstance(pos, (Path, str)):
        pos_array = pos
    else:
        pos = Path(pos)
        if pos.suffix != '.gdf':
            raise ValueError('Currently only supporting reading positions from .gdf files. '
                             'Consider generating them using, for instance, Gephi.')
        s = ''  # read the node definition from the file
        with pos.open() as f:
            f.readline()
            for line in f:
                if line.startswith('edgedef>'):
                    break
                s += line
        from io import StringIO
        df = pd.read_csv(StringIO(s), header=-1)
        pos_array = df[[4, 5]].values

    # convert to dictionary
    pos = {n: [p[0], p[1]] for n, p in enumerate(pos_array)}

    # uniform color
    if isinstance(colors, str) and is_color_like(colors):
        colors = [colors for c in range(len(node_labels))]

    # color degree of the graph
    if isinstance(colors, str) and colors.startswith('degree'):
        # see also tools.paga.paga_degrees
        if colors == 'degree_dashed':
            colors = [d for _, d in nx_g_dashed.degree(weight='weight')]
        elif colors == 'degree_solid':
            colors = [d for _, d in nx_g_solid.degree(weight='weight')]
        else:
            raise ValueError('`degree` either "degree_dashed" or "degree_solid".')
        colors = (np.array(colors) - np.min(colors)) / (np.max(colors) - np.min(colors))

    # plot gene expression
    var_names = adata.var_names if adata.raw is None else adata.raw.var_names
    if isinstance(colors, str) and colors in var_names:
        x_color = []
        cats = adata.obs[groups_key].cat.categories
        for icat, cat in enumerate(cats):
            subset = (cat == adata.obs[groups_key]).values
            if adata.raw is not None and use_raw:
                adata_gene = adata.raw[:, colors]
            else:
                adata_gene = adata[:, colors]
            x_color.append(np.mean(adata_gene.X[subset]))
        colors = x_color

    # plot continuous annotation
    if isinstance(colors, str) and colors in adata.obs and not is_categorical_dtype(adata.obs[colors]):
        x_color = []
        cats = adata.obs[groups_key].cat.categories
        for icat, cat in enumerate(cats):
            subset = (cat == adata.obs[groups_key]).values
            x_color.append(adata.obs.loc[subset, colors].mean())
        colors = x_color

    # plot categorical annotation
    if isinstance(colors, str) and colors in adata.obs and is_categorical_dtype(adata.obs[colors]):
        from scanpy._utils import compute_association_matrix_of_groups, get_associated_colors_of_groups
        norm = 'reference' if normalize_to_color else 'prediction'
        asso_names, asso_matrix = \
            compute_association_matrix_of_groups(adata, prediction=groups_key, reference=colors, normalization=norm)
        _utils.add_colors_for_categorical_sample_annotation(adata, colors)
        asso_colors = get_associated_colors_of_groups(adata.uns[colors + '_colors'], asso_matrix)
        colors = asso_colors

    if len(colors) < len(node_labels):
        raise ValueError('`color` list need to be at least as long as `groups`/`node_labels` list.')

    # count number of connected components
    n_components, labels = scipy.sparse.csgraph.connected_components(adjacency_solid)
    if n_components > 1 and single_component:
        component_sizes = np.bincount(labels)
        largest_component = np.where(component_sizes == component_sizes.max())[0][0]
        adjacency_solid = adjacency_solid.tocsr()[labels == largest_component, :]
        adjacency_solid = adjacency_solid.tocsc()[:, labels == largest_component]
        colors = np.array(colors)[labels == largest_component]
        node_labels = np.array(node_labels)[labels == largest_component]
        cats_dropped = adata.obs[groups_key].cat.categories[labels != largest_component].tolist()
        logg.info(f'Restricting graph to largest connected component by dropping categories\n{cats_dropped}')
        nx_g_solid = nx.Graph(adjacency_solid)
        if dashed_edges is not None:
            raise ValueError('`single_component` only if `dashed_edges` is `None`.')

    # groups sizes
    if groups_key is not None and groups_key + '_sizes' in adata.uns:
        groups_sizes = adata.uns[groups_key + '_sizes']
    else:
        groups_sizes = np.ones(len(node_labels))
    base_scale_scatter = 2000
    base_pie_size = (base_scale_scatter / (np.sqrt(adjacency_solid.shape[0]) + 10) * node_size_scale)
    median_group_size = np.median(groups_sizes)
    groups_sizes = base_pie_size * np.power(groups_sizes / median_group_size, node_size_power)

    # edge widths
    base_edge_width = edge_width_scale * 5 * rcParams['lines.linewidth']

    # draw dashed edges
    if dashed_edges is not None:
        widths = [x[-1]['weight'] for x in nx_g_dashed.edges(data=True)]
        widths = base_edge_width * np.array(widths)
        if max_edge_width is not None:
            widths = np.clip(widths, None, max_edge_width)
        nx.draw_networkx_edges(nx_g_dashed, pos, ax=ax, width=widths, edge_color='grey', style='dashed', alpha=0.5)

    # draw solid edges
    if transitions is None:
        widths = [x[-1]['weight'] for x in nx_g_solid.edges(data=True)]
        widths = base_edge_width * np.array(widths)
        if min_edge_width is not None or max_edge_width is not None:
            widths = np.clip(widths, min_edge_width, max_edge_width)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            nx.draw_networkx_edges(nx_g_solid, pos, ax=ax, width=widths, edge_color='black')

    # draw directed edges
    else:
        adjacency_transitions = adata.uns['paga'][transitions].copy()
        if threshold is None: threshold = 0.01
        adjacency_transitions.data[adjacency_transitions.data < threshold] = 0
        adjacency_transitions.eliminate_zeros()
        g_dir = nx.DiGraph(adjacency_transitions.T)
        widths = [x[-1]['weight'] for x in g_dir.edges(data=True)]
        widths = base_edge_width * np.array(widths)
        if min_edge_width is not None or max_edge_width is not None:
            widths = np.clip(widths, min_edge_width, max_edge_width)
        nx.draw_networkx_edges(g_dir, pos, ax=ax, width=widths, edge_color='k',
                               arrowsize=arrowsize, arrowstyle='-|>', node_size=groups_sizes)

    if export_to_gexf:
        if isinstance(colors[0], tuple):
            from matplotlib.colors import rgb2hex
            colors = [rgb2hex(c) for c in colors]
        for count, n in enumerate(nx_g_solid.nodes()):
            nx_g_solid.node[count]['label'] = str(node_labels[count])
            nx_g_solid.node[count]['color'] = str(colors[count])
            nx_g_solid.node[count]['viz'] = dict(position=dict(x=1000 * pos[count][0], y=1000 * pos[count][1], z=0))
        filename = settings.writedir / 'paga_graph.gexf'
        logg.warn(f'exporting to {filename}')
        settings.writedir.mkdir(parents=True, exist_ok=True)
        nx.write_gexf(nx_g_solid, settings.writedir / 'paga_graph.gexf')

    ax.set_frame_on(frameon)
    ax.set_xticks([])
    ax.set_yticks([])

    if fontsize is None:
        fontsize = rcParams['legend.fontsize']
    if fontoutline is not None:
        text_kwds = dict(text_kwds)
        text_kwds['path_effects'] = [patheffects.withStroke(linewidth=fontoutline, foreground='w')]
    # usual scatter plot
    if not isinstance(colors[0], cabc.Mapping):
        n_groups = len(pos_array)
        sct = ax.scatter(pos_array[:, 0], pos_array[:, 1], s=groups_sizes, cmap=cmap,
                         c=colors[:n_groups], edgecolors='face', zorder=2)
        for count, group in enumerate(node_labels):
            ax.text(pos_array[count, 0], pos_array[count, 1], group, verticalalignment='center',
                    horizontalalignment='center', size=fontsize, fontweight=fontweight, **text_kwds)
    # else pie chart plot
    else:
        # start with this dummy plot... otherwise strange behavior
        sct = ax.scatter(pos_array[:, 0], pos_array[:, 1], c='white', edgecolors='face', s=groups_sizes, cmap=cmap)
        trans = ax.transData.transform
        bbox = ax.get_position().get_points()
        ax_x_min = bbox[0, 0]
        ax_x_max = bbox[1, 0]
        ax_y_min = bbox[0, 1]
        ax_y_max = bbox[1, 1]
        ax_len_x = ax_x_max - ax_x_min
        ax_len_y = ax_y_max - ax_y_min
        trans2 = ax.transAxes.inverted().transform
        pie_axs = []
        for count, n in enumerate(nx_g_solid.nodes()):
            pie_size = groups_sizes[count] / base_scale_scatter
            x1, y1 = trans(pos[n])     # data coordinates
            xa, ya = trans2((x1, y1))  # axis coordinates
            xa = ax_x_min + (xa - pie_size/2) * ax_len_x
            ya = ax_y_min + (ya - pie_size/2) * ax_len_y
            # clip, the fruchterman layout sometimes places below figure
            if ya < 0: ya = 0
            if xa < 0: xa = 0
            pie_axs.append(pl.axes([xa, ya, pie_size * ax_len_x, pie_size * ax_len_y], frameon=False))
            pie_axs[count].set_xticks([])
            pie_axs[count].set_yticks([])
            if not isinstance(colors[count], cabc.Mapping):
                raise ValueError(
                    f'{colors[count]} is neither a dict of valid '
                    'matplotlib colors nor a valid matplotlib color.'
                )
            color_single = colors[count].keys()
            fracs = [colors[count][c] for c in color_single]
            if sum(fracs) < 1:
                color_single = list(color_single)
                color_single.append('grey')
                fracs.append(1-sum(fracs))
            pie_axs[count].pie(fracs, colors=color_single)
        if node_labels is not None:
            for ia, a in enumerate(pie_axs):
                a.text(0.5, 0.5, node_labels[ia], verticalalignment='center', horizontalalignment='center',
                       transform=a.transAxes, size=fontsize, fontweight=fontweight, **text_kwds)
    return sct
