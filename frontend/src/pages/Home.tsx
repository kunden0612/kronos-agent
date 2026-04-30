import React, { useState, useRef, useEffect } from 'react';
import { Layout, Button, Input, Card, List, Avatar, Typography, Spin, message, Space, Alert } from 'antd';
import { SendOutlined, RobotOutlined, UserOutlined, LogoutOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { useNavigate } from 'react-router-dom';
import { chatApi, ChatResponse, PredictResponse } from '../services/api';
import { useAppStore } from '../store';

const { Header, Content, Sider } = Layout;
const { TextArea } = Input;
const { Title, Text } = Typography;

const Home: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAppStore();
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string>();
  const [messages, setMessages] = useState<any[]>([]);
  const [currentPrediction, setCurrentPrediction] = useState<PredictResponse | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (text: string) => {
    if (!text.trim() || loading) return;

    const userMessage = {
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await chatApi.sendMessage({
        message: text,
        conversation_id: conversationId,
      });

      const assistantMessage = {
        role: 'assistant',
        content: response.data.message,
        timestamp: response.data.timestamp,
        prediction: response.data.prediction,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setConversationId(response.data.conversation_id);

      if (response.data.prediction) {
        setCurrentPrediction(response.data.prediction);
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '发送失败');
    } finally {
      setLoading(false);
    }
  };

  const renderChart = () => {
    if (!currentPrediction) return null;

    const predictions = currentPrediction.predictions;
    const dates = predictions.map(p => p.timestamp.substring(0, 10));
    const closeValues = predictions.map(p => p.close);
    const lowValues = predictions.map(p => p.confidence.low_95);
    const highValues = predictions.map(p => p.confidence.high_95);

    const option = {
      tooltip: {
        trigger: 'axis',
      },
      xAxis: {
        type: 'category',
        data: dates,
      },
      yAxis: {
        type: 'value',
      },
      series: [
        {
          name: '预测收盘价',
          type: 'line',
          data: closeValues,
          smooth: true,
          lineStyle: { color: '#1677ff', width: 3 },
          itemStyle: { color: '#1677ff' },
        },
        {
          name: '置信区间',
          type: 'line',
          data: lowValues,
          smooth: true,
          lineStyle: { opacity: 0 },
          itemStyle: { opacity: 0 },
          stack: 'confidence',
        },
        {
          name: '',
          type: 'line',
          data: highValues,
          smooth: true,
          lineStyle: { opacity: 0 },
          itemStyle: { opacity: 0 },
          stack: 'confidence',
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(22, 119, 255, 0.3)' },
                { offset: 1, color: 'rgba(22, 119, 255, 0.1)' },
              ],
            },
          },
        },
      ],
    };

    return (
      <Card title="预测图表" style={{ marginBottom: 16 }}>
        <ReactECharts option={option} style={{ height: 300 }} />
        <Alert
          message="风险提示"
          description={currentPrediction.risk_warning}
          type="warning"
          showIcon
          style={{ marginTop: 16 }}
        />
        {currentPrediction.interpretation && (
          <Card title="AI 解读" style={{ marginTop: 16 }}>
            <Text>{currentPrediction.interpretation}</Text>
          </Card>
        )}
      </Card>
    );
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <RobotOutlined style={{ fontSize: 24, color: '#1677ff', marginRight: 12 }} />
          <Title level={4} style={{ margin: 0 }}>Hermes-Kronos</Title>
        </div>
        <Space>
          <Text>欢迎，{user?.email}</Text>
          <Button icon={<LogoutOutlined />} onClick={handleLogout}>
            退出
          </Button>
        </Space>
      </Header>
      <Layout>
        <Content style={{ display: 'flex', height: 'calc(100vh - 64px)' }}>
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 16, background: '#f5f5f5' }}>
            {renderChart()}
            <Card style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
              <Title level={5} style={{ marginBottom: 16 }}>智能对话</Title>
              <List
                style={{ flex: 1, overflowY: 'auto', marginBottom: 16 }}
                dataSource={messages}
                renderItem={(msg) => (
                  <List.Item style={{ justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                    <div style={{
                      maxWidth: '70%',
                      background: msg.role === 'user' ? '#1677ff' : '#fff',
                      color: msg.role === 'user' ? '#fff' : '#333',
                      padding: '12px 16px',
                      borderRadius: 8,
                      boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 4 }}>
                        <Avatar icon={msg.role === 'user' ? <UserOutlined /> : <RobotOutlined />} size="small" style={{ marginRight: 8 }} />
                        <Text style={{ fontSize: 12, color: msg.role === 'user' ? 'rgba(255,255,255,0.8)' : '#999' }}>
                          {msg.role === 'user' ? '我' : 'Kronos'}
                        </Text>
                      </div>
                      <Text style={{ color: msg.role === 'user' ? '#fff' : '#333', whiteSpace: 'pre-wrap' }}>
                        {msg.content}
                      </Text>
                    </div>
                  </List.Item>
                )}
              />
              <div ref={messagesEndRef} />
              <div style={{ display: 'flex', gap: 8 }}>
                <TextArea
                  placeholder="输入消息，比如：预测茅台未来5天的走势"
                  autoSize={{ minRows: 2, maxRows: 6 }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage(e.currentTarget.value);
                      e.currentTarget.value = '';
                    }
                  }}
                  onPressEnter={(e) => {
                    if (!e.shiftKey) {
                      e.preventDefault();
                      const text = e.currentTarget.value;
                      e.currentTarget.value = '';
                      handleSendMessage(text);
                    }
                  }}
                />
                <Button
                  type="primary"
                  icon={<SendOutlined />}
                  loading={loading}
                  style={{ height: 'auto', alignSelf: 'flex-end' }}
                  onClick={() => {
                    const textArea = document.querySelector('textarea') as HTMLTextAreaElement;
                    const text = textArea?.value || '';
                    if (textArea) textArea.value = '';
                    handleSendMessage(text);
                  }}
                >
                  发送
                </Button>
              </div>
            </Card>
          </div>
        </Content>
      </Layout>
    </Layout>
  );
};

export default Home;
