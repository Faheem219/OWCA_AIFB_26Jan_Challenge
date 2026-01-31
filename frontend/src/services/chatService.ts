/**
 * Chat service for messaging and conversation management
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

interface Conversation {
    id: string;
    other_participant: {
        id: string;
        name: string;
    };
    product_id?: string;
    last_message: {
        content: string;
        timestamp: string | null;
    };
    unread_count: number;
    updated_at: string | null;
}

interface Message {
    id: string;
    sender_id: string;
    content: string;
    translated_content?: string;
    type: 'text' | 'image' | 'voice' | 'offer' | 'offer_response';
    created_at: string;
}

interface Offer {
    id: string;
    product_id: string;
    price: number;
    quantity: number;
    total_amount: number;
    status: 'pending' | 'accepted' | 'rejected' | 'countered';
}

const getAuthHeaders = () => {
    const token = localStorage.getItem('accessToken');
    return {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
    };
};

export const chatService = {
    /**
     * Get all conversations for the current user
     */
    async getConversations(): Promise<{ conversations: Conversation[]; total_count: number }> {
        const response = await fetch(`${API_BASE_URL}/chat/conversations`, {
            headers: getAuthHeaders(),
        });
        if (!response.ok) {
            throw new Error('Failed to fetch conversations');
        }
        return response.json();
    },

    /**
     * Create a new conversation
     */
    async createConversation(participantId: string, productId?: string): Promise<Conversation> {
        const response = await fetch(`${API_BASE_URL}/chat/conversations`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                participant_id: participantId,
                product_id: productId,
            }),
        });
        if (!response.ok) {
            throw new Error('Failed to create conversation');
        }
        const data = await response.json();
        
        // Return a proper Conversation object from backend response
        return {
            id: data.id || data.conversation_id,
            other_participant: data.other_participant || { id: participantId, name: 'Unknown' },
            product_id: data.product_id || productId,
            last_message: data.last_message || { content: '', timestamp: null },
            unread_count: data.unread_count || 0,
            updated_at: data.updated_at || new Date().toISOString(),
        };
    },

    /**
     * Get messages from a conversation
     */
    async getMessages(
        conversationId: string,
        limit: number = 50,
        skip: number = 0
    ): Promise<{ messages: Message[]; total_count: number; has_more: boolean }> {
        const response = await fetch(
            `${API_BASE_URL}/chat/conversations/${conversationId}/messages?limit=${limit}&skip=${skip}`,
            { headers: getAuthHeaders() }
        );
        if (!response.ok) {
            throw new Error('Failed to fetch messages');
        }
        return response.json();
    },

    /**
     * Send a message in a conversation
     */
    async sendMessage(
        conversationId: string,
        content: string,
        type: string = 'text',
        translateTo?: string
    ): Promise<Message> {
        const response = await fetch(`${API_BASE_URL}/chat/conversations/${conversationId}/messages`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                content,
                type,
                translate_to: translateTo,
            }),
        });
        if (!response.ok) {
            throw new Error('Failed to send message');
        }
        return response.json();
    },

    /**
     * Make a price offer in a conversation
     */
    async makeOffer(
        conversationId: string,
        productId: string,
        price: number,
        quantity: number,
        message?: string
    ): Promise<Offer> {
        const response = await fetch(`${API_BASE_URL}/chat/conversations/${conversationId}/offers`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                product_id: productId,
                price,
                quantity,
                message,
            }),
        });
        if (!response.ok) {
            throw new Error('Failed to make offer');
        }
        return response.json();
    },

    /**
     * Respond to an offer
     */
    async respondToOffer(
        offerId: string,
        action: 'accept' | 'reject' | 'counter',
        counterPrice?: number
    ): Promise<{ id: string; status: string; message: string }> {
        const response = await fetch(`${API_BASE_URL}/chat/offers/${offerId}`, {
            method: 'PUT',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                action,
                counter_price: counterPrice,
            }),
        });
        if (!response.ok) {
            throw new Error('Failed to respond to offer');
        }
        return response.json();
    },

    /**
     * Get AI negotiation suggestion
     */
    async getAiSuggestion(
        conversationId: string,
        currentPrice: number,
        marketAverage: number,
        commodity: string
    ): Promise<{ suggested_price: number; reasoning: string; negotiation_tips: string[] }> {
        const response = await fetch(`${API_BASE_URL}/chat/conversations/${conversationId}/ai-suggestion`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                current_price: currentPrice,
                market_average: marketAverage,
                commodity,
            }),
        });
        if (!response.ok) {
            throw new Error('Failed to get AI suggestion');
        }
        return response.json();
    },

    /**
     * Create a WebSocket connection for real-time chat
     */
    createWebSocketConnection(conversationId: string): WebSocket {
        const wsUrl = API_BASE_URL.replace('http', 'ws').replace('/api/v1', '');
        return new WebSocket(`${wsUrl}/api/v1/chat/ws/${conversationId}`);
    },
};

export default chatService;
