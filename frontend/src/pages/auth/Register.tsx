
import { useState } from 'react';
import { Card, Form, Input, Button, message, Typography } from 'antd';
import { UserOutlined, MailOutlined, LockOutlined } from '@ant-design/icons';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { authApi } from '../../api/auth';

const { Title, Text } = Typography;

export default function Register() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const onFinish = async (values: any) => {
    setLoading(true);
    try {
      await authApi.register({
        username: values.username,
        email: values.email,
        password: values.password,
      });
      message.success(t('auth.registerSuccess'));
      navigate('/login');
    } catch (err: any) {
      message.error(err.response?.data?.detail || t('auth.registerFailed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <Card className="auth-card">
        <Title level={2}>{t('auth.register')}</Title>
        <Form name="register" onFinish={onFinish} layout="vertical" size="large">
          <Form.Item
            name="username"
            rules={[
              { required: true, message: t('auth.usernameRequired') },
              { min: 3, max: 20, message: t('auth.usernameLength') },
              { pattern: /^[a-zA-Z0-9_]+$/, message: t('auth.usernamePattern') },
            ]}
          >
            <Input prefix={<UserOutlined />} placeholder={t('auth.usernamePlaceholder')} />
          </Form.Item>
          <Form.Item
            name="email"
            rules={[
              { required: true, message: t('auth.emailRequired') },
              { type: 'email', message: t('auth.emailInvalid') },
            ]}
          >
            <Input prefix={<MailOutlined />} placeholder={t('auth.emailPlaceholder')} />
          </Form.Item>
          <Form.Item
            name="password"
            rules={[
              { required: true, message: t('auth.passwordRequired') },
              { min: 8, max: 32, message: t('auth.passwordLength') },
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder={t('auth.passwordPlaceholder')} />
          </Form.Item>
          <Form.Item
            name="confirmPassword"
            dependencies={['password']}
            rules={[
              { required: true, message: t('auth.confirmPasswordRequired') },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) return Promise.resolve();
                  return Promise.reject(new Error(t('auth.passwordMismatch')));
                },
              }),
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder={t('auth.confirmPasswordPlaceholder')} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              {t('auth.register')}
            </Button>
          </Form.Item>
        </Form>
        <div style={{ textAlign: 'center' }}>
          <Text>{t('auth.hasAccount')} <Link to="/login">{t('auth.login')}</Link></Text>
        </div>
      </Card>
    </div>
  );
}
