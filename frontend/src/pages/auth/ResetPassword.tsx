
import { useState } from 'react';
import { Card, Form, Input, Button, message, Typography } from 'antd';
import { LockOutlined } from '@ant-design/icons';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { authApi } from '../../api/auth';

const { Title } = Typography;

export default function ResetPassword() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(false);
  const token = searchParams.get('token') || '';

  const onFinish = async (values: any) => {
    setLoading(true);
    try {
      await authApi.resetPassword(token, values.new_password);
      message.success(t('auth.passwordResetSuccess'));
      navigate('/login');
    } catch (err: any) {
      message.error(err.response?.data?.detail || t('auth.passwordResetFailed'));
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="auth-container">
        <Card className="auth-card">
          <Title level={2}>{t('auth.invalidResetLink')}</Title>
          <div style={{ textAlign: 'center' }}>
            <Link to="/login">{t('auth.backToLogin')}</Link>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <Card className="auth-card">
        <Title level={2}>{t('auth.resetPassword')}</Title>
        <Form name="reset" onFinish={onFinish} layout="vertical" size="large">
          <Form.Item
            name="new_password"
            rules={[
              { required: true, message: t('auth.passwordRequired') },
              { min: 8, max: 32, message: t('auth.passwordLength') },
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder={t('auth.newPassword')} />
          </Form.Item>
          <Form.Item
            name="confirm_password"
            dependencies={['new_password']}
            rules={[
              { required: true, message: t('auth.confirmPasswordRequired') },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('new_password') === value) return Promise.resolve();
                  return Promise.reject(new Error(t('auth.passwordMismatch')));
                },
              }),
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder={t('auth.confirmPasswordPlaceholder')} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              {t('auth.resetPassword')}
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
