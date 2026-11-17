import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import '../api/models.dart' as api;
import '../state/providers.dart';
import '../theme/tokens.dart';
import 'ui.dart';

/// Bottom sheet for "wrong result?" and for naming an unknown reciter.
/// Returns the reciter the user picked, if any, so it can be shown at once.
Future<api.ReciterSummary?> showFeedbackSheet(
  BuildContext context, {
  required String identifyId,
  required String initialKind,
}) => showModalBottomSheet<api.ReciterSummary>(
  context: context,
  isScrollControlled: true,
  backgroundColor: context.colors.surface,
  shape: const RoundedRectangleBorder(
    borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
  ),
  builder: (_) =>
      _FeedbackSheet(identifyId: identifyId, initialKind: initialKind),
);

class _FeedbackSheet extends ConsumerStatefulWidget {
  const _FeedbackSheet({required this.identifyId, required this.initialKind});

  final String identifyId;
  final String initialKind;

  @override
  ConsumerState<_FeedbackSheet> createState() => _FeedbackSheetState();
}

enum _Send { idle, sending, sent, failed }

class _FeedbackSheetState extends ConsumerState<_FeedbackSheet> {
  late String _kind = widget.initialKind;
  final _surah = TextEditingController();
  final _ayah = TextEditingController();
  api.ReciterSummary? _reciter;
  _Send _state = _Send.idle;

  @override
  void dispose() {
    _surah.dispose();
    _ayah.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() => _state = _Send.sending);
    final surah = int.tryParse(_surah.text) ?? 0;
    final ayah = int.tryParse(_ayah.text) ?? 0;
    final withPlace =
        _kind == 'wrong_ayah' && surah >= 1 && surah <= 114 && ayah >= 1;
    final picked = _kind == 'wrong_reciter' ? _reciter : null;
    try {
      await ref
          .read(apiProvider)
          .sendFeedback(
            api.FeedbackReport(
              identifyId: widget.identifyId,
              kind: _kind,
              correctSurah: withPlace ? surah : null,
              correctAyah: withPlace ? ayah : null,
              correctReciterId: picked?.id,
            ),
          );
      if (!mounted) return;
      setState(() => _state = _Send.sent);
      await Future<void>.delayed(const Duration(milliseconds: 900));
      if (mounted) Navigator.of(context).pop(picked);
    } catch (_) {
      if (mounted) setState(() => _state = _Send.failed);
    }
  }

  InputDecoration _field(BuildContext context, String label) {
    final c = context.colors;
    OutlineInputBorder border(Color color) => OutlineInputBorder(
      borderRadius: BorderRadius.circular(16),
      borderSide: BorderSide(color: color),
    );
    return InputDecoration(
      labelText: label,
      labelStyle: ts(13, color: c.muted),
      filled: true,
      fillColor: c.bg,
      enabledBorder: border(c.border),
      focusedBorder: border(c.accent),
    );
  }

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final t = context.t;
    final reciters = ref.watch(recitersProvider).value ?? const [];
    final kinds = [
      ('wrong_ayah', t.feedbackWrongAyah),
      ('wrong_reciter', t.feedbackWrongReciter),
      ('other', t.feedbackOther),
    ];
    final digits = [
      FilteringTextInputFormatter.digitsOnly,
      LengthLimitingTextInputFormatter(3),
    ];

    return Padding(
      padding: EdgeInsets.fromLTRB(
        20,
        20,
        20,
        24 + MediaQuery.of(context).viewInsets.bottom,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Expanded(
                child: Semantics(
                  header: true,
                  child: Text(
                    widget.initialKind == 'wrong_reciter'
                        ? t.feedbackReciterTitle
                        : t.feedbackTitle,
                    style: ts(18, weight: FontWeight.w700),
                  ),
                ),
              ),
              CircleIconButton(
                icon: Icons.close_rounded,
                label: t.commonClose,
                onPressed: () => Navigator.of(context).pop(),
              ),
            ],
          ),
          if (_state == _Send.sent)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 32),
              child: Semantics(
                liveRegion: true,
                child: Text(
                  t.feedbackThanks,
                  textAlign: TextAlign.center,
                  style: ts(16, weight: FontWeight.w600, color: c.accent),
                ),
              ),
            )
          else ...[
            const SizedBox(height: 16),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final (value, label) in kinds)
                  ChoiceChipButton(
                    label: label,
                    selected: _kind == value,
                    onTap: () => setState(() => _kind = value),
                  ),
              ],
            ),
            const SizedBox(height: 16),
            if (_kind == 'wrong_ayah')
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _surah,
                      keyboardType: TextInputType.number,
                      inputFormatters: digits,
                      decoration: _field(
                        context,
                        '${t.feedbackSurahNumber} (${t.feedbackOptional})',
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextField(
                      controller: _ayah,
                      keyboardType: TextInputType.number,
                      inputFormatters: digits,
                      decoration: _field(
                        context,
                        '${t.feedbackAyahNumber} (${t.feedbackOptional})',
                      ),
                    ),
                  ),
                ],
              ),
            if (_kind == 'wrong_reciter')
              DropdownButtonFormField<api.ReciterSummary>(
                initialValue: _reciter,
                isExpanded: true,
                dropdownColor: c.surface2,
                decoration: _field(
                  context,
                  '${t.feedbackChooseReciter} (${t.feedbackOptional})',
                ),
                items: [
                  for (final r in reciters)
                    DropdownMenuItem(value: r, child: Text(r.nameAr)),
                ],
                onChanged: (r) => setState(() => _reciter = r),
              ),
            const SizedBox(height: 12),
            Text(t.feedbackNote, style: ts(12, color: c.muted)),
            if (_state == _Send.failed)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Semantics(
                  liveRegion: true,
                  child: Text(
                    t.feedbackFailed,
                    style: ts(13, color: c.warning),
                  ),
                ),
              ),
            const SizedBox(height: 16),
            PrimaryButton(
              label: _state == _Send.sending
                  ? t.feedbackSending
                  : t.feedbackSend,
              onPressed: _state == _Send.sending ? null : _submit,
            ),
          ],
        ],
      ),
    );
  }
}
