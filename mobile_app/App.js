import React, { useState, useRef } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TextInput,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  StatusBar,
  SafeAreaView,
} from 'react-native';

// ─── CONFIG ───────────────────────────────────────────────────
// Physical Phone (Expo Go) → use your PC's Wi-Fi IP
const API_BASE_URL = 'http://192.168.29.145:8000';
// ──────────────────────────────────────────────────────────────

export default function App() {
  const [url, setUrl] = useState('');
  const [inputLang, setInputLang] = useState('english');
  const [outputLang, setOutputLang] = useState('english');

  const [isLoading, setIsLoading] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState('');
  const [sessionData, setSessionData] = useState(null);

  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [showTranscript, setShowTranscript] = useState(false);
  const chatScrollRef = useRef(null);

  const processVideo = async () => {
    if (!url.trim()) {
      alert('Please paste a YouTube URL first.');
      return;
    }
    setIsLoading(true);
    setLoadingStatus('Transcribing & Summarising (~1 min)…');

    try {
      const response = await fetch(`${API_BASE_URL}/process-video`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source: url.trim(),
          input_lang: inputLang.trim() || 'english',
          output_lang: outputLang.trim() || 'english',
        }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || `Server error ${response.status}`);
      }

      const data = await response.json();
      setSessionData(data);
      setChatHistory([
        {
          role: 'ai',
          text: `Hi! I've processed "${data.title}".\n\nAsk me anything about it!`,
        },
      ]);
    } catch (error) {
      alert('Error: ' + error.message);
    }

    setIsLoading(false);
    setLoadingStatus('');
  };

  const sendChatMessage = async () => {
    if (!chatMessage.trim() || !sessionData?.session_id) return;

    const userMsg = chatMessage.trim();
    setChatMessage('');
    setChatHistory(prev => [...prev, { role: 'user', text: userMsg }]);
    setIsChatLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionData.session_id,
          question: userMsg,
        }),
      });
      const data = await response.json();
      setChatHistory(prev => [...prev, { role: 'ai', text: data.answer }]);
    } catch {
      setChatHistory(prev => [
        ...prev,
        { role: 'ai', text: "Couldn't reach the server. Is the backend running?" },
      ]);
    }

    setIsChatLoading(false);
    setTimeout(() => chatScrollRef.current?.scrollToEnd({ animated: true }), 100);
  };

  const reset = () => {
    setSessionData(null);
    setChatHistory([]);
    setUrl('');
    setInputLang('english');
    setOutputLang('english');
  };

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="light-content" backgroundColor="#0F172A" />
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>🎬 AI Video Assistant</Text>
          {sessionData && (
            <TouchableOpacity onPress={reset} style={styles.newBtn}>
              <Text style={styles.newBtnText}>+ New</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* INPUT SCREEN */}
        {!sessionData && (
          <ScrollView contentContainerStyle={styles.screen}>
            <Text style={styles.tagline}>
              Drop any YouTube link. Chat with the video in your language.
            </Text>

            <View style={styles.card}>
              <Text style={styles.label}>YouTube URL</Text>
              <TextInput
                style={styles.input}
                placeholder="https://youtu.be/..."
                placeholderTextColor="#4B5563"
                value={url}
                onChangeText={setUrl}
                autoCapitalize="none"
                autoCorrect={false}
              />

              <View style={styles.row}>
                <View style={{ flex: 1, marginRight: 10 }}>
                  <Text style={styles.label}>Video Language</Text>
                  <TextInput
                    style={styles.input}
                    placeholder="e.g. bengali"
                    placeholderTextColor="#4B5563"
                    value={inputLang}
                    onChangeText={setInputLang}
                  />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.label}>Output Language</Text>
                  <TextInput
                    style={styles.input}
                    placeholder="e.g. english"
                    placeholderTextColor="#4B5563"
                    value={outputLang}
                    onChangeText={setOutputLang}
                  />
                </View>
              </View>

              <TouchableOpacity
                style={[styles.btn, isLoading && styles.btnDisabled]}
                onPress={processVideo}
                disabled={isLoading}
              >
                {isLoading ? (
                  <View style={styles.loadingRow}>
                    <ActivityIndicator color="#fff" size="small" />
                    <Text style={[styles.btnText, { marginLeft: 10 }]}>{loadingStatus}</Text>
                  </View>
                ) : (
                  <Text style={styles.btnText}>Process Video ▶</Text>
                )}
              </TouchableOpacity>
            </View>
          </ScrollView>
        )}

        {/* RESULTS SCREEN */}
        {sessionData && (
          <View style={{ flex: 1 }}>
            <ScrollView contentContainerStyle={styles.screen}>
              <View style={styles.card}>
                <Text style={styles.videoTitle}>{sessionData.title}</Text>
                <View style={styles.divider} />
                <Text style={styles.sectionLabel}>📋 Summary</Text>
                <Text style={styles.bodyText}>{sessionData.summary}</Text>

                {sessionData.action_items &&
                  sessionData.action_items !== 'No action items found.' && (
                    <>
                      <View style={styles.divider} />
                      <Text style={styles.sectionLabel}>✅ Action Items</Text>
                      <Text style={styles.bodyText}>{sessionData.action_items}</Text>
                    </>
                  )}
              </View>

              {/* Full Transcript */}
              <View style={styles.card}>
                <TouchableOpacity
                  style={styles.transcriptToggle}
                  onPress={() => setShowTranscript(prev => !prev)}
                >
                  <Text style={styles.sectionLabel}>📝 Full Transcript</Text>
                  <Text style={styles.toggleIcon}>{showTranscript ? '▲ Hide' : '▼ Show'}</Text>
                </TouchableOpacity>
                {showTranscript && (
                  <Text style={[styles.bodyText, { marginTop: 10 }]}>
                    {sessionData.transcript}
                  </Text>
                )}
              </View>

              {/* Chat */}
              <View style={styles.chatCard}>
                <Text style={styles.sectionLabel}>💬 Chat with Video</Text>
                <ScrollView
                  ref={chatScrollRef}
                  style={styles.chatHistory}
                  onContentSizeChange={() =>
                    chatScrollRef.current?.scrollToEnd({ animated: true })
                  }
                >
                  {chatHistory.map((msg, idx) => (
                    <View
                      key={idx}
                      style={[
                        styles.bubble,
                        msg.role === 'user' ? styles.userBubble : styles.aiBubble,
                      ]}
                    >
                      <Text
                        style={[
                          styles.bubbleText,
                          msg.role === 'user' ? styles.userText : styles.aiText,
                        ]}
                      >
                        {msg.text}
                      </Text>
                    </View>
                  ))}
                  {isChatLoading && (
                    <View style={[styles.bubble, styles.aiBubble]}>
                      <ActivityIndicator size="small" color="#7C3AED" />
                    </View>
                  )}
                </ScrollView>

                <View style={styles.chatInputRow}>
                  <TextInput
                    style={styles.chatInput}
                    placeholder="Ask anything…"
                    placeholderTextColor="#4B5563"
                    value={chatMessage}
                    onChangeText={setChatMessage}
                    onSubmitEditing={sendChatMessage}
                    returnKeyType="send"
                  />
                  <TouchableOpacity style={styles.sendBtn} onPress={sendChatMessage}>
                    <Text style={styles.sendBtnText}>↑</Text>
                  </TouchableOpacity>
                </View>
              </View>
            </ScrollView>
          </View>
        )}
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const PURPLE = '#7C3AED';
const SURFACE = '#1E293B';
const BG = '#0F172A';

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: BG },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#1E293B',
  },
  headerTitle: { fontSize: 18, fontWeight: '700', color: '#fff' },
  newBtn: { backgroundColor: PURPLE, paddingHorizontal: 14, paddingVertical: 6, borderRadius: 20 },
  newBtnText: { color: '#fff', fontWeight: '600', fontSize: 13 },

  screen: { padding: 20, paddingBottom: 40 },
  tagline: { color: '#94A3B8', fontSize: 15, textAlign: 'center', marginBottom: 24, lineHeight: 22 },

  card: {
    backgroundColor: SURFACE,
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOpacity: 0.4,
    shadowRadius: 12,
    elevation: 6,
  },
  chatCard: {
    backgroundColor: SURFACE,
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    height: 440,
  },

  label: { color: '#94A3B8', fontSize: 12, fontWeight: '600', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.5 },
  input: {
    backgroundColor: BG,
    color: '#fff',
    borderRadius: 10,
    padding: 12,
    fontSize: 15,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#334155',
  },
  row: { flexDirection: 'row' },

  btn: { backgroundColor: PURPLE, padding: 16, borderRadius: 12, alignItems: 'center', marginTop: 4 },
  btnDisabled: { opacity: 0.6 },
  btnText: { color: '#fff', fontWeight: '700', fontSize: 16 },
  loadingRow: { flexDirection: 'row', alignItems: 'center' },

  videoTitle: { fontSize: 20, fontWeight: '700', color: '#fff', marginBottom: 12 },
  divider: { height: 1, backgroundColor: '#334155', marginVertical: 16 },
  sectionLabel: { color: PURPLE, fontWeight: '700', fontSize: 14, marginBottom: 10, textTransform: 'uppercase', letterSpacing: 0.5 },
  bodyText: { color: '#CBD5E1', fontSize: 14, lineHeight: 22 },

  chatHistory: { flex: 1, marginBottom: 12 },
  bubble: { padding: 12, borderRadius: 14, marginBottom: 8, maxWidth: '85%' },
  userBubble: { backgroundColor: PURPLE, alignSelf: 'flex-end', borderBottomRightRadius: 2 },
  aiBubble: { backgroundColor: '#334155', alignSelf: 'flex-start', borderBottomLeftRadius: 2 },
  bubbleText: { fontSize: 14, lineHeight: 20 },
  userText: { color: '#fff' },
  aiText: { color: '#E2E8F0' },

  chatInputRow: { flexDirection: 'row', alignItems: 'center' },
  chatInput: {
    flex: 1,
    backgroundColor: BG,
    color: '#fff',
    padding: 12,
    borderRadius: 10,
    marginRight: 8,
    borderWidth: 1,
    borderColor: '#334155',
    fontSize: 14,
  },
  sendBtn: { backgroundColor: PURPLE, width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center' },
  transcriptToggle: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  toggleIcon: { color: '#94A3B8', fontSize: 12, fontWeight: '600' },
  sendBtnText: { color: '#fff', fontSize: 20, fontWeight: '700' },
});
