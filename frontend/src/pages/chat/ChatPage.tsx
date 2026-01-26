import React, { useState, useEffect, useRef } from 'react';
import {
    Container,
    Typography,
    Box,
    Paper,
    List,
    ListItem,
    ListItemText,
    ListItemAvatar,
    Avatar,
    TextField,
    IconButton,
    Divider,
    Badge,
    CircularProgress,
    Chip,
    Alert,
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import PersonIcon from '@mui/icons-material/Person';
import TranslateIcon from '@mui/icons-material/Translate';
import { chatService } from '../../services/chatService';
import { useAuth } from '../../hooks/useAuth';

interface Conversation {
    id: string;
    other_participant: { id: string; name: string };
    product_id?: string;
    last_message: { content: string; timestamp: string | null };
    unread_count: number;
    updated_at: string | null;
}

interface Message {
    id: string;
    sender_id: string;
    content: string;
    translated_content?: string;
    type: string;
    created_at: string;
}

export const ChatPage: React.FC = () => {
    const { user } = useAuth();
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [newMessage, setNewMessage] = useState('');
    const [loading, setLoading] = useState(true);
    const [sendingMessage, setSendingMessage] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        loadConversations();
    }, []);

    useEffect(() => {
        if (selectedConversation) {
            loadMessages(selectedConversation.id);
        }
    }, [selectedConversation]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const loadConversations = async () => {
        try {
            setLoading(true);
            const data = await chatService.getConversations();
            setConversations(data.conversations);
        } catch (err) {
            setError('Failed to load conversations');
        } finally {
            setLoading(false);
        }
    };

    const loadMessages = async (conversationId: string) => {
        try {
            const data = await chatService.getMessages(conversationId);
            setMessages(data.messages);
        } catch (err) {
            setError('Failed to load messages');
        }
    };

    const handleSendMessage = async () => {
        if (!newMessage.trim() || !selectedConversation) return;

        try {
            setSendingMessage(true);
            const message = await chatService.sendMessage(selectedConversation.id, newMessage);
            setMessages((prev) => [...prev, message]);
            setNewMessage('');
        } catch (err) {
            setError('Failed to send message');
        } finally {
            setSendingMessage(false);
        }
    };

    const formatTime = (dateString: string | null) => {
        if (!dateString) return '';
        return new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    if (loading) {
        return (
            <Container maxWidth="lg">
                <Box sx={{ py: 4, display: 'flex', justifyContent: 'center' }}>
                    <CircularProgress />
                </Box>
            </Container>
        );
    }

    return (
        <Container maxWidth="lg">
            <Box sx={{ py: 4 }}>
                <Typography variant="h4" gutterBottom>
                    Messages
                </Typography>

                {error && (
                    <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
                        {error}
                    </Alert>
                )}

                <Paper sx={{ display: 'flex', height: '70vh' }}>
                    {/* Conversations List */}
                    <Box sx={{ width: 300, borderRight: 1, borderColor: 'divider', overflow: 'auto' }}>
                        <Typography variant="h6" sx={{ p: 2 }}>
                            Conversations
                        </Typography>
                        <Divider />
                        {conversations.length === 0 ? (
                            <Box sx={{ p: 2, textAlign: 'center' }}>
                                <Typography color="text.secondary">No conversations yet</Typography>
                            </Box>
                        ) : (
                            <List>
                                {conversations.map((conv) => (
                                    <ListItem
                                        key={conv.id}
                                        button
                                        selected={selectedConversation?.id === conv.id}
                                        onClick={() => setSelectedConversation(conv)}
                                    >
                                        <ListItemAvatar>
                                            <Badge badgeContent={conv.unread_count} color="primary">
                                                <Avatar>
                                                    <PersonIcon />
                                                </Avatar>
                                            </Badge>
                                        </ListItemAvatar>
                                        <ListItemText
                                            primary={conv.other_participant.name}
                                            secondary={conv.last_message.content || 'No messages'}
                                            secondaryTypographyProps={{ noWrap: true }}
                                        />
                                    </ListItem>
                                ))}
                            </List>
                        )}
                    </Box>

                    {/* Chat Area */}
                    <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                        {selectedConversation ? (
                            <>
                                {/* Chat Header */}
                                <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
                                    <Typography variant="h6">
                                        {selectedConversation.other_participant.name}
                                    </Typography>
                                </Box>

                                {/* Messages */}
                                <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
                                    {messages.map((msg) => (
                                        <Box
                                            key={msg.id}
                                            sx={{
                                                display: 'flex',
                                                justifyContent: msg.sender_id === user?.id ? 'flex-end' : 'flex-start',
                                                mb: 1,
                                            }}
                                        >
                                            <Paper
                                                sx={{
                                                    p: 1.5,
                                                    maxWidth: '70%',
                                                    bgcolor: msg.sender_id === user?.id ? 'primary.main' : 'grey.100',
                                                    color: msg.sender_id === user?.id ? 'primary.contrastText' : 'text.primary',
                                                }}
                                            >
                                                <Typography variant="body1">{msg.content}</Typography>
                                                {msg.translated_content && (
                                                    <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                                        <TranslateIcon fontSize="small" />
                                                        <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                                                            {msg.translated_content}
                                                        </Typography>
                                                    </Box>
                                                )}
                                                {msg.type === 'offer' && (
                                                    <Chip label="Price Offer" size="small" sx={{ mt: 0.5 }} />
                                                )}
                                                <Typography variant="caption" sx={{ display: 'block', mt: 0.5, opacity: 0.7 }}>
                                                    {formatTime(msg.created_at)}
                                                </Typography>
                                            </Paper>
                                        </Box>
                                    ))}
                                    <div ref={messagesEndRef} />
                                </Box>

                                {/* Message Input */}
                                <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider', display: 'flex', gap: 1 }}>
                                    <TextField
                                        fullWidth
                                        placeholder="Type a message..."
                                        value={newMessage}
                                        onChange={(e) => setNewMessage(e.target.value)}
                                        onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                                        disabled={sendingMessage}
                                        size="small"
                                    />
                                    <IconButton
                                        color="primary"
                                        onClick={handleSendMessage}
                                        disabled={!newMessage.trim() || sendingMessage}
                                    >
                                        {sendingMessage ? <CircularProgress size={24} /> : <SendIcon />}
                                    </IconButton>
                                </Box>
                            </>
                        ) : (
                            <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                <Typography color="text.secondary">
                                    Select a conversation to start messaging
                                </Typography>
                            </Box>
                        )}
                    </Box>
                </Paper>
            </Box>
        </Container>
    );
};