import '../adapters/gloss_lattice_builder.dart';
import '../contracts/gloss_lattice.dart';
import '../integration/segmentation_classification_port.dart';
import 'gloss_lattice_session_coordinator.dart';
import 'gloss_lattice_websocket_client.dart';

/// Packages Esther's completed Stage 5/6 output and sends it exactly once.
///
/// A failed submission remains pending so a reconnect can retransmit the
/// exact same `(session_id, lattice_seq)` bytes, as required by the backend's
/// idempotency rules.
final class GlossLatticeSubmissionService {
  GlossLatticeSubmissionService({
    required this.builder,
    required GlossLatticeWebSocketClient websocketClient,
    required this.sessionCoordinator,
  }) : _websocketClient = websocketClient {
    if (builder.sessionId != websocketClient.sessionId) {
      throw ArgumentError(
        'Builder and WebSocket client must use the same session_id.',
      );
    }
  }

  final GlossLatticeBuilder builder;
  final GlossLatticeSessionCoordinator sessionCoordinator;
  GlossLatticeWebSocketClient _websocketClient;

  GlossLattice? _pendingLattice;
  bool _submissionInProgress = false;

  GlossLattice? get pendingLattice => _pendingLattice;
  GlossLatticeWebSocketClient get websocketClient => _websocketClient;

  Future<GlossLatticeSubmissionReceipt> submit(
    ClassifiedUtteranceOutput output,
  ) async {
    if (_pendingLattice != null) {
      throw StateError(
        'Retry the pending lattice before submitting another utterance.',
      );
    }
    final lattice = builder.build(
      latticeSeq: sessionCoordinator.nextLatticeSeq(),
      utteranceId: output.utteranceId,
      startedAtMs: output.startedAtMs,
      endedAtMs: output.endedAtMs,
      slots: output.slots,
    );
    _pendingLattice = lattice;
    return _sendPending();
  }

  Future<GlossLatticeSubmissionReceipt> retryPending() {
    if (_pendingLattice == null) {
      throw StateError('There is no pending lattice to retry.');
    }
    return _sendPending();
  }

  Future<GlossLatticeSubmissionReceipt> _sendPending() async {
    if (_submissionInProgress) {
      throw StateError('A lattice submission is already in progress.');
    }
    final lattice = _pendingLattice!;
    _submissionInProgress = true;
    try {
      final receipt = await _websocketClient.send(lattice);
      _pendingLattice = null;
      return receipt;
    } finally {
      _submissionInProgress = false;
    }
  }

  /// Rebinds this session after a transport disconnect without rebuilding the
  /// pending lattice. A later [retryPending] therefore sends identical bytes
  /// with the original sequence number.
  Future<void> replaceWebsocketClient(
    GlossLatticeWebSocketClient replacement,
  ) async {
    if (_submissionInProgress) {
      throw StateError('Cannot replace the WebSocket during a submission.');
    }
    if (replacement.sessionId != builder.sessionId) {
      throw ArgumentError(
        'Replacement WebSocket client must use the same session_id.',
      );
    }
    final previous = _websocketClient;
    _websocketClient = replacement;
    await previous.close();
  }

  Future<void> close() => _websocketClient.close();
}
