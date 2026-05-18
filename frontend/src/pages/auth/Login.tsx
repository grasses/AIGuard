
import { useState } from 'react';
import { Card, Form, Input, Button, Checkbox, message, Typography, Space } from 'antd';
import { MailOutlined, LockOutlined } from '@ant-design/icons';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { authApi } from '../../api/auth';
import { useAuthStore } from '../../stores/authStore';

const { Title, Text } = Typography;

export default function Login() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [loading, setLoading] = useState(false);

  const onFinish = async (values: { email: string; password: string; remember: boolean }) => {
    setLoading(true);
    try {
      const res = await authApi.login({
        email: values.email,
        password: values.password,
        remember_me: values.remember,
      });
      const { access_token, refresh_token, user } = res.data.data;
      setAuth(user, access_token, refresh_token);
      message.success(t('auth.loginSuccess'));
      navigate(user.role === 'user' ? '/user/dashboard' : '/admin/dashboard');
    } catch (err: any) {
      message.error(err.response?.data?.detail || t('auth.loginFailed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <Card className="auth-card">
        <Title level={2}>🛡️ {t('app.title')}</Title>
        <Form
          name="login"
          onFinish={onFinish}
          layout="vertical"
          size="large"
          initialValues={{ remember: true }}
        >
          <Form.Item
            name="email"
            rules={[{ required: true, message: t('auth.emailRequired') }]}
          >
            <Input prefix={<MailOutlined />} placeholder={t('auth.emailPlaceholder')} />
          </Form.Item>
          <Form.Item
            name="password"
            rules={[{ required: true, message: t('auth.passwordRequired') }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder={t('auth.passwordPlaceholder')} />
          </Form.Item>
          <Form.Item name="remember" valuePropName="checked">
            <Checkbox>{t('auth.rememberMe')}</Checkbox>
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              {t('auth.login')}
            </Button>
          </Form.Item>
        </Form>
        <div style={{ textAlign: 'center' }}>
          <Space>
            <Link to="/register">{t('auth.register')}</Link>
            <Text type="secondary">|</Text>
            <Link to="/forgot-password">{t('auth.forgotPassword')}</Link>
          </Space>
        </div>
      </Card>
    </div>
  );
}
