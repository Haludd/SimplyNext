import '../adapters/gloss_lattice_builder.dart';
import '../contracts/gloss_lattice_session.dart';
import 'gloss_lattice_connection_factory.dart';
import 'gloss_lattice_session_client.dart';
import 'gloss_lattice_session_coordinator.dart';
import 'gloss_lattice_submission_service.dart';

/// One negotiated frontend-to-backend GlossLattice session.
///
/// This is the composition root for transport: create the HTTP session, open
/// its authenticated WebSocket, bind the exact producer/language profile, and
/// expose the submission service used by the frontend pipeline.
final class GlossLatticeFrontendSession {
  GlossLatticeFrontendSession._({
    required this.negotiated,
    required this.coordinator,
    required this.submissions,
    required this._sessionClient,
    required this._connectionFactory,
  });

  final GlossLatticeSessionCreateResponse negotiated;
  final GlossLatticeSessionCoordinator coordinator;
  final GlossLatticeSubmissionService submissions;
  final GlossLatticeSessionClient _sessionClient;
  final GlossLatticeConnectionFactory _connectionFactory;

  static Future<GlossLatticeFrontendSession> connect({
    required GlossLatticeSessionCreateRequest request,
    required GlossLatticeSessionClient sessionClient,
    GlossLatticeConnectionFactory? connectionFactory,
    GlossLatticeSessionCoordinator? coordinator,
  }) async {
    final sessionCoordinator =
        coordinator ?? GlossLatticeSessionCoordinator.start();
    // The clock is deliberately established before session negotiation.
    sessionCoordinator.nowMs();
    final negotiated = await sessionClient.createSession(request);
    final resolvedConnectionFactory =
        connectionFactory ?? GlossLatticeConnectionFactory();
    final websocket = await resolvedConnectionFactory.connect(
      // Session negotiation and bearer-token use are deliberately pinned
      // to one origin so a token cannot be sent to a different host.
      baseUri: sessionClient.baseUri,
      session: negotiated,
    );
    final builder = GlossLatticeBuilder(
      sessionId: negotiated.sessionId,
      language: request.language,
      producer: request.producer,
    );
    return GlossLatticeFrontendSession._(
      negotiated: negotiated,
      coordinator: sessionCoordinator,
      sessionClient: sessionClient,
      connectionFactory: resolvedConnectionFactory,
      submissions: GlossLatticeSubmissionService(
        builder: builder,
        websocketClient: websocket,
        sessionCoordinator: sessionCoordinator,
      ),
    );
  }

  /// Opens a fresh authenticated socket for the same negotiated session.
  /// Any pending lattice remains byte-for-byte unchanged for cached replay.
  Future<void> reconnect() async {
    final replacement = await _connectionFactory.connect(
      baseUri: _sessionClient.baseUri,
      session: negotiated,
    );
    try {
      await submissions.replaceWebsocketClient(replacement);
    } catch (_) {
      await replacement.close();
      rethrow;
    }
  }

  Future<void> close() => submissions.close();
}
