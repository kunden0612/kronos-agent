import React, { useState } from 'react';
import { Form, Input, Button, Card, message, Tabs } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { authApi } from '../services/api';
import { useAppStore } from '../store';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { setToken, setUser } = useAppStore();
  const [loading, setLoading] = useState(false);

  const handleLogin = async (values: { email: string; password: string }) => {
    setLoading(true);
    try {
      const response = await authApi.login(values.email, values.password);
      const { access_token } = response.data;
      
      setToken(access_token);
      
      const userResponse = await authApi.getMe();
      setUser(userResponse.data);
      
      message.success('登录成功！');
      navigate('/');
    } catch (error: any) {
      message.error(error.response?.data?.detail || '登录失败');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (values: { email: string; password: string }) => {
    setLoading(true);
    try {
      await authApi.register(values.email, values.password);
      message.success('注册成功，请登录！');
    } catch (error: any) {
      message.error(error.response?.data?.detail || '注册失败');
    } finally {
      setLoading(false);
    }
  };

  const loginForm = (
    <Form name="login" onFinish={handleLogin} autoComplete="off">
      <Form.Item
        name="email"
        rules={[{ required: true, message: '请输入邮箱' }, { type: 'email', message: '请输入有效的邮箱' }]}
      >
        <Input prefix={<UserOutlined />} placeholder="邮箱" size="large" />
      </Form.Item>
      <Form.Item
        name="password"
        rules={[{ required: true, message: '请输入密码' }, { min: 6, message: '密码至少6位' }]}
      >
        <Input.Password prefix={<LockOutlined />} placeholder="密码" size="large" />
      </Form.Item>
      <Form.Item>
        <Button type="primary" htmlType="submit" size="large" loading={loading} block>
          登录
        </Button>
      </Form.Item>
    </Form>
  );

  const registerForm = (
    <Form name="register" onFinish={handleRegister} autoComplete="off">
      <Form.Item
        name="email"
        rules={[{ required: true, message: '请输入邮箱' }, { type: 'email', message: '请输入有效的邮箱' }]}
      >
        <Input prefix={<UserOutlined />} placeholder="邮箱" size="large" />
      </Form.Item>
      <Form.Item
        name="password"
        rules={[{ required: true, message: '请输入密码' }, { min: 6, message: '密码至少6位' }]}
      >
        <Input.Password prefix={<LockOutlined />} placeholder="密码" size="large" />
      </Form.Item>
      <Form.Item>
        <Button type="primary" htmlType="submit" size="large" loading={loading} block>
          注册
        </Button>
      </Form.Item>
    </Form>
  );

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    }}>
      <Card style={{ width: 400 }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <h1 style={{ fontSize: 24, fontWeight: 600 }}>Hermes-Kronos</h1>
          <p style={{ color: '#666', marginTop: 8 }}>智能金融预测系统</p>
        </div>
        <Tabs defaultActiveKey="login" centered items={[
          { key: 'login', label: '登录', children: loginForm },
          { key: 'register', label: '注册', children: registerForm },
        ]} />
      </Card>
    </div>
  );
};

export default Login;
