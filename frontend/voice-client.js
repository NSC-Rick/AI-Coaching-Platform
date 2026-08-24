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
        config,
        dynamicVariables,
        onConnect,
        onDisconnect,
        onError,
        onModeChange,
        onStatusChange,
        onMessage
    } = options;

    console.log('[VOICE] Starting ElevenLabs conversation with official SDK v1.21.0');
    console.log('[VOICE] Signed URL present:', Boolean(signedUrl));
    console.log('[VOICE] Signed URL length:', signedUrl?.length);
    console.log('[VOICE] Backend runtime config present:', Boolean(config));

    // Map backend-generated config to the SDK option names.
    // The backend returns conversation_config_override in snake_case;
    // the SDK expects overrides (conversation config) and customLlmExtraBody
    // as top-level session options.
    const overrides = config?.conversation_config_override
        ? {
            agent: {
                prompt: config.conversation_config_override.agent?.prompt
            }
        }
        : undefined;

    const customLlmExtraBody = config?.conversation_config_override?.agent?.custom_llm_extra_body;
    const userId = config?.user_id;

    const promptText = config?.conversation_config_override?.agent?.prompt?.prompt;
    console.log('[VOICE] Prompt override present:', Boolean(promptText));
    console.log('[VOICE] Prompt length:', promptText ? promptText.length : 0);
    console.log('[VOICE] Pathway context marker present:', promptText ? promptText.includes('PATHWAY CONTEXT FOR THIS SESSION') : false);
    console.log('[VOICE] Client context marker present:', promptText ? promptText.includes('CURRENT CLIENT CONTEXT') : false);
    console.log('[VOICE] customLlmExtraBody present:', Boolean(customLlmExtraBody));
    console.log('[VOICE] app session id:', customLlmExtraBody ? customLlmExtraBody.app_session_id : undefined);
    console.log('[VOICE] overrides passed to SDK:', Boolean(overrides));
    console.log('[VOICE] user id:', userId);
    console.log('[VOICE] Dynamic variables:', dynamicVariables);

    try {
        console.log('[VOICE] Calling Conversation.startSession');
        
        const startOptions = {
            signedUrl,
            dynamicVariables,
            ...(overrides ? { overrides } : {}),
            ...(customLlmExtraBody ? { customLlmExtraBody } : {}),
            ...(userId ? { userId } : {}),
            
            // Connection lifecycle callbacks
            onConnect: (data) => {
                console.log('[VOICE] ✓ onConnect fired');
                console.log('[VOICE] Connection data:', data);
                if (data?.conversationId) {
                    console.log('[VOICE] Conversation ID:', data.conversationId);
                }
                if (onConnect) onConnect(data);
            },
            
            onDisconnect: () => {
                console.log('[VOICE] ✗ onDisconnect fired');
                if (onDisconnect) onDisconnect();
            },
            
            onError: (error) => {
                console.error('[VOICE] ✗ onError fired');
                console.error('[VOICE] Error type:', typeof error);
                console.error('[VOICE] Error name:', error?.name);
                console.error('[VOICE] Error message:', error?.message);
                console.error('[VOICE] Error object:', error);
                if (error?.stack) {
                    console.error('[VOICE] Error stack:', error.stack);
                }
                if (onError) onError(error);
            },
            
            // Status and mode tracking
            onStatusChange: (status) => {
                console.log('[VOICE] Status change:', status);
                if (onStatusChange) onStatusChange(status);
            },
            
            onModeChange: (mode) => {
                console.log('[VOICE] Mode change:', mode);
                console.log('[VOICE] Mode value:', mode?.mode);
                if (onModeChange) onModeChange(mode);
            },
            
            // Message tracking
            onMessage: (message) => {
                console.log('[VOICE] Message received:', {
                    type: message?.type,
                    role: message?.role,
                    hasContent: Boolean(message?.content)
                });
                if (onMessage) onMessage(message);
            },
            
            // Debug callback for detailed diagnostics
            onDebug: (event) => {
                console.log('[VOICE] Debug event:', event);
            }
        };

        console.log('[VOICE] SDK start options prepared:', {
            hasOverrides: Boolean(startOptions.overrides),
            hasCustomLlmExtraBody: Boolean(startOptions.customLlmExtraBody),
            hasUserId: Boolean(startOptions.userId)
        });

        const conversation = await Conversation.startSession(startOptions);

        console.log('[VOICE] ✓ startSession resolved successfully');
        console.log('[VOICE] Conversation object created:', Boolean(conversation));
        console.log('[VOICE] Conversation type:', typeof conversation);
        
        return conversation;
        
    } catch (error) {
        console.error('[VOICE] ✗ startSession REJECTED');
        console.error('[VOICE] Rejection error name:', error?.name);
        console.error('[VOICE] Rejection error message:', error?.message);
        console.error('[VOICE] Rejection error:', error);
        if (error?.stack) {
            console.error('[VOICE] Rejection stack:', error.stack);
        }
        throw error;
    }
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
