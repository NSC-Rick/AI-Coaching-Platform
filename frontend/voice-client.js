/**
 * Voice Client Module
 * 
 * Wraps the official @elevenlabs/client SDK for use in the AI Coaching Platform.
 * This module is bundled and served locally to avoid CDN/CORS issues.
 */

import { Conversation } from '@elevenlabs/client';

/**
 * Start an ElevenLabs voice conversation with a signed URL
 * 
 * @param {Object} options - Conversation options
 * @param {string} options.signedUrl - Signed URL from backend
 * @param {Function} options.onConnect - Called when conversation connects
 * @param {Function} options.onDisconnect - Called when conversation disconnects
 * @param {Function} options.onError - Called on error
 * @param {Function} options.onModeChange - Called when mode changes (speaking/listening)
 * @returns {Promise<Object>} Conversation instance
 */
export async function startVoiceConversation(options) {
    const {
        signedUrl,
        onConnect,
        onDisconnect,
        onError,
        onModeChange
    } = options;

    console.log('[VOICE] Starting ElevenLabs conversation with official SDK v1.21.0');

    const conversation = await Conversation.startSession({
        signedUrl,
        onConnect: (data) => {
            console.log('[VOICE] Conversation connected:', data);
            if (onConnect) onConnect(data);
        },
        onDisconnect: () => {
            console.log('[VOICE] Conversation disconnected');
            if (onDisconnect) onDisconnect();
        },
        onError: (error) => {
            console.error('[VOICE] Connection error:', error);
            console.error('[VOICE] Error stack:', error.stack);
            if (onError) onError(error);
        },
        onModeChange: (mode) => {
            console.log('[VOICE] Mode change:', mode.mode);
            if (onModeChange) onModeChange(mode);
        }
    });

    console.log('[VOICE] Conversation started successfully');
    return conversation;
}

/**
 * End an ElevenLabs voice conversation
 * 
 * @param {Object} conversation - Conversation instance from startVoiceConversation
 * @returns {Promise<void>}
 */
export async function endVoiceConversation(conversation) {
    if (!conversation) {
        console.warn('[VOICE] No conversation to end');
        return;
    }

    console.log('[VOICE] Ending conversation');
    await conversation.endSession();
    console.log('[VOICE] Conversation ended');
}

// Log that the module is loaded
console.log('[VOICE] ElevenLabs SDK module ready (v1.21.0)');
