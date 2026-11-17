import 'package:material_ui/material_ui.dart';

import '../widgets/ui.dart';

/// The full mushaf reader is out of scope for v1.
class MushafScreen extends StatelessWidget {
  const MushafScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final t = context.t;
    return Scaffold(
      bottomNavigationBar: const BottomNav(current: NavTab.mushaf),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: Center(
                child: StateMessage(
                  icon: Icons.menu_book_outlined,
                  title: '${t.mushafTitle} · ${t.commonSoon}',
                  body: t.mushafBody,
                ),
              ),
            ),
            const PlayerBar(),
          ],
        ),
      ),
    );
  }
}
