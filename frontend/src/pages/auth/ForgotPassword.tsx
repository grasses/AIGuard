
import { useState } from 'react';
import { Card, Form, Input, Button, message, Typography } from 'antd';
import { MailOutlined } from '@ant-design/icons';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { authApi } from '../../api/auth';

const { Title, Text } = Typography;

export default function ForgotPassword() {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const onFinish = async (values: { email: string }) => {
    setLoading(true);
    try {
      await authApi.forgotPassword(values.email);
      setSent(true);
      message.success(t('auth.resetEmailSent'));
    } catch {
      message.error(t('auth.resetEmailFailed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <Card className="auth-card">
        <Title level={2}>{t('auth.forgotPassword')}</Title>
        {sent ? (
          <div style={{ textAlign: 'center' }}>
            <Text>{t('auth.checkEmail')}</Text>
            <br /><br />
            <Link to="/login">{t('auth.backToLogin')}</Link>
          </div>
        ) : (
          <Form name="forgot" onFinish={onFinish} layout="vertical" size="large">
            <Form.Item
              name="email"
              rules={[
                { required: true, message: t('auth.emailRequired') },
                { type: 'email', message: t('auth.emailInvalid') },
              ]}
            >
              <Input prefix={<MailOutlined />} placeholder={t('auth.emailPlaceholder')} />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading} block>
                {t('auth.sendResetEmail')}
              </Button>
            </Form.Item>
          </Form>
        )}
        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <Link to="/login">{t('auth.backToLogin')}</Link>
        </div>
      </Card>
    </div>
  );
}
