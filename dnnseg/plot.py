import sys
import numpy as np
import librosa
import librosa.display
import pandas as pd
import matplotlib
matplotlib.use('Agg')
from matplotlib import ticker, pyplot as plt
import seaborn as sns
from .data import extract_segment_timestamps
from .util import stderr


def plot_acoustic_features_old(
        inputs,
        targets_bwd=None,
        preds_bwd=None,
        preds_bwd_attn=None,
        targets_fwd=None,
        preds_fwd=None,
        preds_fwd_attn=None,
        segmentation_probs=None,
        segmentation_probs_smoothed=None,
        segmentations=None,
        states=None,
        target_means=None,
        sr=16000,
        hop_length=160,
        drop_zeros=True,
        cmap='Blues',
        titles=None,
        label_map=None,
        char_map=None,
        directory='./',
        prefix='',
        suffix='.png'
):
    time_tick_formatter = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(x * hop_length/sr))

    if titles is None:
        titles = [None] * inputs.shape[0]

    if label_map is not None:
        label_map = dict(zip(label_map.source,label_map.target))

    has_targets_bwd = targets_bwd is not None
    has_preds_bwd = preds_bwd is not None
    has_preds_bwd_attn = preds_bwd_attn is not None
    has_targets_fwd = targets_fwd is not None
    has_preds_fwd = preds_fwd is not None
    has_preds_fwd_attn = preds_fwd_attn is not None
    has_means = target_means is not None
    has_segs = segmentation_probs is not None
    has_smoothing = segmentations is None or segmentation_probs_smoothed is not None
    has_states = states is not None
    n_states = len(states) if has_states else 0

    fig = plt.figure()

    n_plots = 1
    if has_means:
        n_plots += 1
    if has_segs:
        n_plots += 2
        if has_smoothing:
            n_plots += 1
    if has_states:
        n_plots += n_states
    if has_targets_bwd:
        n_plots += 1
    if has_preds_bwd:
        n_plots += 1
    if has_preds_bwd_attn:
        n_plots += 1
    if has_targets_fwd:
        n_plots += 1
    if has_preds_fwd:
        n_plots += 1
    if has_preds_fwd_attn:
        n_plots += 1

    fig.set_size_inches(10, 3 * n_plots)
    axes = []
    for i in range(n_plots):
        axes.append(fig.add_subplot(n_plots, 1, i+1))

    ax_input = axes[0]
    plot_ix = 1

    if has_segs:
        ax_seg = axes[plot_ix]
        plot_ix += 1
        ax_seg_hard = axes[plot_ix]
        plot_ix += 1
        if has_smoothing:
            ax_seg_smoothed = axes[plot_ix]
            plot_ix += 1

    if has_means:
        ax_targ_means = axes[plot_ix]
        plot_ix += 1

    if has_states:
        ax_states = []
        for i in range(n_states):
            ax_states.append(axes[plot_ix])
            plot_ix += 1

    if has_preds_bwd_attn:
        ax_pred_bwd_attn = axes[plot_ix]
        plot_ix += 1

        if has_preds_bwd and has_preds_fwd:
            plot_name = 'Temporal attention (Backward)'
        else:
            plot_name = 'Temporal attention'

        preds_bwd_attn_cur = np.swapaxes(preds_bwd_attn, -2, -1)

        if preds_bwd_attn_cur.shape[-1] > 0:
            librosa.display.specshow(
                preds_bwd_attn_cur,
                sr=sr,
                hop_length=hop_length,
                fmax=8000,
                x_axis='time',
                cmap='Greys',
                ax=ax_pred_bwd_attn
            )
        ax_pred_bwd_attn.set_title(plot_name)
    if has_targets_bwd:
        ax_targ_bwd = axes[plot_ix]
        plot_ix += 1
    if has_preds_bwd:
        ax_pred_bwd = axes[plot_ix]
        plot_ix += 1

    if has_preds_fwd_attn:
        ax_pred_fwd_attn = axes[plot_ix]
        plot_ix += 1

        if has_preds_bwd and has_preds_fwd:
            plot_name = 'Temporal attention (Forward)'
        else:
            plot_name = 'Temporal attention'

        preds_fwd_attn_cur = np.swapaxes(preds_fwd_attn, -2, -1)

        if preds_fwd_attn_cur.shape[-1] > 0:
            librosa.display.specshow(
                preds_fwd_attn_cur,
                sr=sr,
                hop_length=hop_length,
                fmax=8000,
                x_axis='time',
                cmap='Greys',
                ax=ax_pred_fwd_attn
            )
        ax_pred_fwd_attn.set_title(plot_name)
    if has_targets_fwd:
        ax_targ_fwd = axes[plot_ix]
        plot_ix += 1
    if has_preds_fwd:
        ax_pred_fwd = axes[plot_ix]
        plot_ix += 1

    for i in range(len(inputs)):
        inputs_cur = inputs[i]
        if drop_zeros:
            inputs_select = np.where(np.any(inputs_cur[:,:-1] != 0., axis=1))[0]
            inputs_cur = inputs_cur[inputs_select]
        inputs_cur = np.swapaxes(inputs_cur, -2, -1)

        librosa.display.specshow(
            inputs_cur,
            sr=sr,
            hop_length=hop_length,
            fmax=8000,
            x_axis='time',
            cmap=cmap,
            ax=ax_input
        )
        ax_input.set_title('Inputs')

        if has_segs:
            segmentation_probs_cur = segmentation_probs[i]
            if drop_zeros:
                segmentation_probs_cur = segmentation_probs_cur[inputs_select]

            segmentation_probs_cur = np.swapaxes(segmentation_probs_cur, -2, -1)

            if segmentations is None:
                segmentations_cur = segmentation_probs_cur
            else:
                segmentations_cur = segmentations[i]
                if drop_zeros:
                    segmentations_cur = segmentations_cur[inputs_select]
                segmentations_cur = np.swapaxes(segmentations_cur, -2, -1)

            df = pd.DataFrame(
                segmentation_probs_cur,
                index=list(range(1, segmentation_probs_cur.shape[0] + 1))
            )

            pcm = ax_seg.pcolormesh(df, cmap='Greys', vmin=0., vmax=1.)
            ax_seg.xaxis.set_major_formatter(time_tick_formatter)
            ax_seg.set_yticks(np.arange(0.5, len(df.index), 1), minor=False)
            ax_seg.set_yticklabels(df.index)
            ax_seg.set_xlabel('Time')
            ax_seg.set_title('Segmentation Probabilities')

            colors = [plt.get_cmap('gist_rainbow')(1. * j / len(segmentation_probs_cur)) for j in range(len(segmentation_probs_cur))]
            segs_hard = []

            if segmentations is None:
                smoothing_algorithm = 'rbf'
                n_points = 1000
            else:
                smoothing_algorithm = None
                n_points = None

            for j, s in enumerate(segmentations_cur):
                timestamps, basis, segs_smoothed = extract_segment_timestamps(
                    s,
                    algorithm=smoothing_algorithm,
                    n_points=n_points,
                    seconds_per_step=float(hop_length)/sr,
                    return_plot=True
                )
                if segmentation_probs_smoothed is not None:
                    segs_smoothed = segmentation_probs_smoothed[i][:,j]
                    if drop_zeros:
                        segs_smoothed = segs_smoothed[inputs_select]
                segs_hard.append(timestamps)
                if has_smoothing:
                    ax_seg_smoothed.plot(basis, segmentation_probs_cur[j], color=list(colors[j][:-1]) + [0.5], linestyle=':', label='L%d source' %(j+1))
                    ax_seg_smoothed.plot(basis, segs_smoothed, color=colors[j], label='L%d smoothed' %(j+1))
                # _, _, w, _ = ax_seg_hard.get_window_extent().bounds
                # linewidth = w / len(segs_smoothed)
                ax_seg_hard.vlines(timestamps, j, j+1, color='k', linewidth=1)

            if has_smoothing:
                ax_seg_smoothed.set_xlim(0., basis[-1])
                ax_seg_smoothed.legend(fancybox=True, framealpha=0.75, frameon=True, facecolor='white', edgecolor='gray')
                ax_seg_smoothed.set_xlabel('Time')
                ax_seg_smoothed.set_title('Smoothed Segmentations')

            ax_seg_hard.set_xlim(0., basis[-1])
            ax_seg_hard.set_ylim(0., n_states - 1)
            ax_seg_hard.set_yticks(np.arange(0.5, len(df.index), 1), minor=False)
            ax_seg_hard.set_yticklabels(df.index)
            ax_seg_hard.set_xlabel('Time')
            ax_seg_hard.set_title('Hard segmentations')

        if has_states:
            for j in range(n_states):
                states_cur = states[j][i]

                if drop_zeros:
                    states_cur = states_cur[inputs_select]

                states_cur = np.swapaxes(states_cur, -2, -1)

                librosa.display.specshow(
                    states_cur,
                    sr=sr,
                    hop_length=hop_length,
                    fmax=8000,
                    x_axis='time',
                    cmap=cmap,
                    ax=ax_states[j]
                )
                ax_states[j].set_title('Hidden States (%s)' %(j+1))

        if has_means:
            target_means_cur = target_means[i]
            if drop_zeros:
                target_means_select = np.where(np.any(target_means_cur[:,:-1] != 0., axis=1))[0]
                target_means_cur = target_means_cur[target_means_select]
            target_means_cur = np.swapaxes(target_means_cur, -2, -1)

            librosa.display.specshow(
                target_means_cur,
                sr=sr,
                hop_length=hop_length,
                fmax=8000,
                x_axis='time',
                cmap=cmap,
                ax=ax_targ_means
            )
            ax_targ_means.set_title('Target means')

        if has_targets_bwd:
            if has_targets_bwd and has_targets_fwd:
                plot_name = 'Targets (Backward)'
            else:
                plot_name = 'Targets'

            targets_cur = targets_bwd[i]
            if drop_zeros:
                targets_select = np.where(np.any(targets_cur[:,:-1] != 0., axis=1))[0]
                targets_cur = targets_cur[targets_select]
            targets_cur = np.swapaxes(targets_cur, -2, -1)

            if targets_cur.shape[-1] > 0:
                librosa.display.specshow(
                    targets_cur,
                    sr=sr,
                    hop_length=hop_length,
                    fmax=8000,
                    x_axis='time',
                    cmap=cmap,
                    ax=ax_targ_bwd
                )
            ax_targ_bwd.set_title(plot_name)

        if has_preds_bwd:
            if has_preds_bwd and has_preds_fwd:
                plot_name = 'Predictions (Backward)'
            else:
                plot_name = 'Predictions'

            preds_cur = preds_bwd[i]
            if drop_zeros:
                if has_targets_bwd:
                    preds_select = targets_select
                else:
                    preds_select = np.where(np.any(preds_cur[:,:-1] != 0., axis=1))[0]
                preds_cur = preds_cur[preds_select]
            preds_cur = np.swapaxes(preds_cur, -2, -1)

            if preds_cur.shape[-1] > 0:
                librosa.display.specshow(
                    preds_cur,
                    sr=sr,
                    hop_length=hop_length,
                    fmax=8000,
                    x_axis='time',
                    cmap=cmap,
                    ax=ax_pred_bwd
                )
            ax_pred_bwd.set_title(plot_name)

        if has_targets_fwd:
            if has_targets_bwd and has_targets_fwd:
                plot_name = 'Targets (Forward)'
            else:
                plot_name = 'Targets'

            targets_cur = targets_fwd[i]
            if drop_zeros:
                targets_select = np.where(np.any(targets_cur[:,:-1] != 0., axis=1))[0]
                targets_cur = targets_cur[targets_select]
            targets_cur = np.swapaxes(targets_cur, -2, -1)

            if targets_cur.shape[-1] > 0:
                librosa.display.specshow(
                    targets_cur,
                    sr=sr,
                    hop_length=hop_length,
                    fmax=8000,
                    x_axis='time',
                    cmap=cmap,
                    ax=ax_targ_fwd
                )
            ax_targ_fwd.set_title(plot_name)

        if has_preds_fwd:
            if has_preds_bwd and has_preds_fwd:
                plot_name = 'Predictions (Forward)'
            else:
                plot_name = 'Predictions'

            preds_cur = preds_fwd[i]
            if drop_zeros:
                if has_targets_fwd:
                    preds_select = targets_select
                else:
                    preds_select = np.where(np.any(preds_cur != 0., axis=1))[0]
                preds_cur = preds_cur[preds_select]
            preds_cur = np.swapaxes(preds_cur, -2, -1)

            if preds_cur.shape[-1] > 0:
                librosa.display.specshow(
                    preds_cur,
                    sr=sr,
                    hop_length=hop_length,
                    fmax=8000,
                    x_axis='time',
                    cmap=cmap,
                    ax=ax_pred_fwd
                )
            ax_pred_fwd.set_title(plot_name)

        if titles[i] is not None:
            title = titles[i]
            if label_map is not None:
                title = label_map.get(title, title)
            fig.suptitle(title, fontsize=20, weight='bold')
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        try:
            fig.savefig(directory + '/' + prefix + '%d_featureplot' % i + suffix)
        except Exception:
            stderr('IO error when saving plot. Skipping plotting...\n')

        ax_input.clear()
        if has_segs:
            ax_seg.clear()
            ax_seg_hard.clear()
            if has_smoothing:
                ax_seg_smoothed.clear()
        if has_states:
            for ax in ax_states:
                ax.clear()
        if has_means:
            ax_targ_means.clear()
        if has_targets_bwd:
            ax_targ_bwd.clear()
        if has_preds_bwd:
            ax_pred_bwd.clear()
        if has_targets_fwd:
            ax_targ_fwd.clear()
        if has_preds_fwd:
            ax_pred_fwd.clear()

    plt.close(fig)


def plot_acoustic_features(
        inputs,
        states=None,
        segmentation_probs=None,
        segmentation_probs_smoothed=None,
        segmentations=None,
        targs=None,
        preds=None,
        positional_encodings=None,
        plot_keys=None,
        sr=16000,
        hop_length=160,
        drop_zeros=False,
        cmap='Blues',
        titles=None,
        label_map=None,
        directory='./',
        prefix='',
        suffix='.png'
):
    time_tick_formatter = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(x * hop_length/sr))

    if titles is None:
        titles = [None] * inputs.shape[0]

    if label_map is not None:
        label_map = dict(zip(label_map.source,label_map.target))

    compute_keys = plot_keys is None

    # Add plot labels if plots are provided as lists
    if compute_keys:
        plot_keys = set()
    if targs is not None:
        if isinstance(targs, list):
            targs = {str(x):y for x, y in zip(range(len(targs)), targs)}
        if compute_keys:
            plot_keys = plot_keys.union(set(targs.keys()))
    if preds is not None:
        if isinstance(preds, list):
            preds = {str(x):y for x, y in zip(range(len(preds)), preds)}
        if compute_keys:
            plot_keys = plot_keys.union(set(preds.keys()))
    if positional_encodings is not None:
        if isinstance(preds, list):
            positional_encodings = {str(x):y for x, y in zip(range(len(positional_encodings)), positional_encodings)}
        if compute_keys:
            plot_keys = plot_keys.union(set(positional_encodings.keys()))

    if compute_keys:
        plot_keys = sorted(list(plot_keys))

    has_segs = segmentation_probs is not None
    has_smoothing = segmentations is None or segmentation_probs_smoothed is not None
    has_states = states is not None
    n_states = len(states) if has_states else 0

    fig = plt.figure()

    n_plots = 1
    if has_segs:
        n_plots += 2
        if has_smoothing:
            n_plots += 1
    if has_states:
        n_plots += n_states
    if targs is not None:
        i = 0
        for x in targs:
            if x in plot_keys:
                i += 1
        n_plots += i
    if preds is not None:
        i = 0
        for x in preds:
            if x in plot_keys:
                i += 1
        n_plots += i
    if positional_encodings is not None:
        i = 0
        for x in positional_encodings:
            if x in plot_keys:
                i += 1
        n_plots += i

    fig.set_size_inches(10, 3 * n_plots)
    axes_src = []
    for i in range(n_plots):
        axes_src.append(fig.add_subplot(n_plots, 1, i+1))

    axes = {}

    axes['input'] = axes_src[0]
    plot_ix = 1

    if has_segs:
        axes['seg'] = axes_src[plot_ix]
        plot_ix += 1
        axes['seg_hard'] = axes_src[plot_ix]
        plot_ix += 1
        if has_smoothing:
            axes['seg_smoothed'] = axes_src[plot_ix]
            plot_ix += 1

    if has_states:
        for i in range(n_states):
            axes['states_%d' % i] = axes_src[plot_ix]
            plot_ix += 1

    for k in plot_keys:
        if targs is not None and k in targs:
            axes['Targets ' + k] = axes_src[plot_ix]
            plot_ix += 1
        if positional_encodings is not None and k in targs:
            axes['Positional Encodings ' + k] = axes_src[plot_ix]
            plot_ix += 1
        if preds is not None and k in targs:
            axes['Predictions ' + k] = axes_src[plot_ix]
            plot_ix += 1

    for i in range(len(inputs)):
        ax = axes['input']
        inputs_cur = inputs[i]
        if drop_zeros:
            inputs_select = np.where(np.any(inputs_cur[:,:-1] != 0., axis=1))[0]
            inputs_cur = inputs_cur[inputs_select]
        inputs_cur = np.swapaxes(inputs_cur, -2, -1)

        librosa.display.specshow(
            inputs_cur,
            sr=sr,
            hop_length=hop_length,
            fmax=8000,
            x_axis='time',
            cmap=cmap,
            ax=ax
        )
        ax.set_title('Inputs')

        if has_segs:
            ax = axes['seg']
            segmentation_probs_cur = segmentation_probs[i]
            if drop_zeros:
                segmentation_probs_cur = segmentation_probs_cur[inputs_select]

            segmentation_probs_cur = np.swapaxes(segmentation_probs_cur, -2, -1)

            if segmentations is None:
                segmentations_cur = segmentation_probs_cur
            else:
                segmentations_cur = segmentations[i]
                if drop_zeros:
                    segmentations_cur = segmentations_cur[inputs_select]
                segmentations_cur = np.swapaxes(segmentations_cur, -2, -1)

            df = pd.DataFrame(
                segmentation_probs_cur,
                index=list(range(1, segmentation_probs_cur.shape[0] + 1))
            )

            pcm = axes['seg'].pcolormesh(df, cmap='Greys', vmin=0., vmax=1.)
            ax.xaxis.set_major_formatter(time_tick_formatter)
            ax.set_yticks(np.arange(0.5, len(df.index), 1), minor=False)
            ax.set_yticklabels(df.index)
            ax.set_xlabel('Time')
            ax.set_title('Segmentation Probabilities')

            ax_h = axes['seg_hard']
            if has_smoothing:
                ax_s = axes['seg_smoothed']
            colors = [plt.get_cmap('gist_rainbow')(1. * j / len(segmentation_probs_cur)) for j in range(len(segmentation_probs_cur))]
            segs_hard = []

            if segmentations is None:
                smoothing_algorithm = 'rbf'
                n_points = 1000
            else:
                smoothing_algorithm = None
                n_points = None

            for j, s in enumerate(segmentations_cur):
                timestamps, basis, segs_smoothed = extract_segment_timestamps(
                    s,
                    algorithm=smoothing_algorithm,
                    n_points=n_points,
                    seconds_per_step=float(hop_length)/sr,
                    return_plot=True
                )
                if segmentation_probs_smoothed is not None:
                    segs_smoothed = segmentation_probs_smoothed[i][:,j]
                    if drop_zeros:
                        segs_smoothed = segs_smoothed[inputs_select]
                segs_hard.append(timestamps)
                if has_smoothing:
                    ax_s.plot(basis, segmentation_probs_cur[j], color=list(colors[j][:-1]) + [0.5], linestyle=':', label='L%d source' %(j+1))
                    ax_s.plot(basis, segs_smoothed, color=colors[j], label='L%d smoothed' %(j+1))
                # _, _, w, _ = ax_seg_hard.get_window_extent().bounds
                # linewidth = w / len(segs_smoothed)
                ax_h.vlines(timestamps, j, j+1, color='k', linewidth=1)

            if has_smoothing:
                ax_s.set_xlim(0., basis[-1])
                ax_s.legend(fancybox=True, framealpha=0.75, frameon=True, facecolor='white', edgecolor='gray')
                ax_s.set_xlabel('Time')
                ax_s.set_title('Smoothed Segmentations')

            ax_h.set_xlim(0., basis[-1])
            ax_h.set_ylim(0., n_states - 1)
            ax_h.set_yticks(np.arange(0.5, len(df.index), 1), minor=False)
            ax_h.set_yticklabels(df.index)
            ax_h.set_xlabel('Time')
            ax_h.set_title('Hard segmentations')

        if has_states:
            for j in range(n_states):
                ax = axes['states_%d' % j]
                states_cur = states[j][i]

                if drop_zeros:
                    states_cur = states_cur[inputs_select]

                states_cur = np.swapaxes(states_cur, -2, -1)

                librosa.display.specshow(
                    states_cur,
                    sr=sr,
                    hop_length=hop_length,
                    fmax=8000,
                    x_axis='time',
                    cmap=cmap,
                    ax=ax
                )
                ax.set_title('Hidden States (%s)' %(j+1))

        for k in plot_keys:
            for j, t in enumerate([targs, positional_encodings, preds]):
                if t is not None and k in t:
                    if j == 0:
                        plot_name = 'Targets '
                    elif j == 1:
                        plot_name = 'Positional Encodings '
                    else:
                        plot_name = 'Predictions '
                    plot_name += k

                    ax = axes[plot_name]

                    arr = t[k][i]
                    if drop_zeros:
                        arr_select = np.where(np.any(arr[:,:-1] != 0., axis=1))[0]
                        arr = arr[arr_select]
                    arr = np.swapaxes(arr, -2, -1)

                    if arr.shape[-1] > 0:
                        librosa.display.specshow(
                            arr,
                            sr=sr,
                            hop_length=hop_length,
                            fmax=8000,
                            x_axis='time',
                            cmap=cmap,
                            ax=ax
                        )
                    ax.set_title(plot_name)

        if titles[i] is not None:
            title = titles[i]
            if label_map is not None:
                title = label_map.get(title, title)
            fig.suptitle(title, fontsize=20, weight='bold')
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        try:
            fig.savefig(directory + '/' + prefix + '%d_featureplot' % i + suffix)
        except Exception:
            stderr('IO error when saving plot. Skipping plotting...\n')

        for ax in axes.values():
            ax.clear()

    plt.close(fig)


def plot_label_histogram(labels, title=None, bins='auto', label_map=None, dir='./', prefix='', suffix='.png'):

    if label_map is not None:
        label_map = dict(zip(label_map.source,label_map.target))

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    labels = pd.Series(labels)
    if label_map is not None:
        labels = labels.replace(label_map)

    ax.hist(labels, bins=bins)

    if title is not None:
        fig.suptitle(title)
    fig.tight_layout()

    try:
        fig.savefig(dir + '/' + prefix + 'label_histogram' + suffix)
    except:
        stderr('IO error when saving plot. Skipping plotting...\n')

    plt.close(fig)

def plot_label_heatmap(labels, preds, title=None, label_map=None, cmap='Blues', dir='./', prefix='', suffix='.png'):
    if label_map is not None:
        label_map = dict(zip(label_map.source,label_map.target))

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    df = pd.crosstab(labels, preds)

    df = pd.DataFrame(np.array(df) / np.array(df).sum(axis=0, keepdims=True), index=df.index, columns=df.columns)
    if label_map is not None:
        index = pd.Series(df.index).replace(label_map)
    else:
        index = df.index
    df.index = index
    df.index.name = None

    fig.set_size_inches(1 + .5 * len(df.columns), .27 * len(df.index))

    ax.pcolormesh(df, cmap=cmap, vmin=0., vmax=1.)
    ax.set_xticks(np.arange(0.5, len(df.columns), 1), minor=False)
    ax.set_xticklabels(df.columns)
    ax.set_yticks(np.arange(0.5, len(df.index), 1), minor=False)
    ax.set_yticklabels(df.index)

    if title is not None:
        fig.suptitle(title)
    # fig.tight_layout()

    try:
        fig.savefig(dir + '/' + prefix + 'label_heatmap' + suffix)
    except:
        stderr('IO error when saving plot. Skipping plotting...\n')

    plt.close(fig)

def plot_binary_unit_heatmap(labels, label_probs, title=None, label_map=None, cmap='Blues', dir='./', prefix='', suffix='.png'):
    if label_map is not None:
        label_map = dict(zip(label_map.source,label_map.target))

    df = {'label': labels}
    for bit in range(label_probs.shape[1]):
        df['%d' %bit] = label_probs[:,bit]

    df = pd.DataFrame(df)
    df = df[~df['label'].isin(['SPN', 'SIL'])]
    df = df.groupby('label').mean()

    if label_map is not None:
        index = pd.Series(df.index).replace(label_map)
    else:
        index = df.index

    df.index = index
    df.index.name = None

    width = 1 + .3 * len(df.columns)
    height = .27 * len(df.index)

    # Correlation-based clustering is undefined if any vectors happen to have no variance.
    # Try correlation first, then fall back to default distance metric if it fails.
    try:
        cm = sns.clustermap(data=df, metric='correlation', cmap=cmap, figsize=(width,height))
    except Exception:
        cm = sns.clustermap(data=df, cmap=cmap, figsize=(width,height))
    cm.cax.set_visible(False)
    cm.ax_col_dendrogram.set_visible(False)

    try:
        cm.savefig(dir + '/' + prefix + 'binary_unit_heatmap' + suffix)
    except Exception:
        stderr('IO error when saving plot. Skipping plotting...\n')

    plt.close('all')


def plot_projections(
        df,
        cmap='hls',
        label_map=None,
        feature_table=None,
        feature_names=None,
        directory='./',
        prefix='',
        suffix='.png'
):
    df = df.copy()

    df['CV'] = df.gold_label.map(lambda x: 'V' if (not x[0] in ['el', 'en'] and x[0] in ['a', 'e', 'i', 'o', 'u']) else 'C')

    if label_map is not None:
        df['IPA'] = df.gold_label.map(label_map)

    if feature_table is not None:
        if not 'gold_label' in feature_table.columns:
            feature_table['gold_label'] = feature_table.label
        df = df.merge(feature_table, on=['gold_label'])

    colors = ['CV']
    if 'IPA' in df.columns:
        colors.append('IPA')
    else:
        colors.append('gold_label')

    if feature_names is not None:
        for c in feature_names:
            df[c] = df[c].map({0: '-', 1: '+'})
        colors += feature_names

    df['Projection 1'] = df.projection1
    df['Projection 2'] = df.projection2

    for c in colors:
        sns.set_style('white')

        with sns.plotting_context(rc={'legend.fontsize': 'small', 'lines.markersize': 2}):
            g = sns.relplot(
                x='Projection 1',
                y='Projection 2',
                kind='scatter',
                hue=c,
                data=df.sort_values(c),
                palette=cmap,
                legend='full',
                size=0.5,
                alpha=0.5
            )
        try:
            g.savefig(directory + '/' + prefix + 'projections_%s' % c + suffix)
        except Exception:
            stderr('IO error when saving plot. Skipping plotting...\n')

        plt.close('all')


