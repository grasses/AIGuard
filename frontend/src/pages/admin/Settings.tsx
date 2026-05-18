
import { useEffect, useState } from 'react';
import { Card, Form, Input, Button, message, Spin } from 'antd';
import { useTranslation } from 'react-i18next';
import apiClient from '../../api/client';

export default function Settings() {
  const { t } = useTranslation();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient.get('/admin/settings').then((res) => {
      form.setFieldsValue(Object.fromEntries(res.data.data.map((s: any) => [s.key, s.value])));
    }).finally(() => setLoading(false));
  }, []);

  const onFinish = async (values: any) => {
    try {
      for (const [key, value] of Object.entries(values)) {
        await apiClient.put('/admin/settings', { key, value });
      }
      message.success(t('common.updateSuccess'));
    } catch {
      message.error(t('common.saveFailed'));
    }
  };

  if (loading) return <Spin />;

  return (
    <div>
      <h2 className="page-header">{t('nav.settings')}</h2>
      <Card>
        <Form form={form} layout="vertical" onFinish={onFinish}>
          <Form.Item name="smtp_host" label="SMTP Host">
            <Input />
          </Form.Item>
          <Form.Item name="smtp_port" label="SMTP Port">
            <Input />
          </Form.Item>
          <Form.Item name="default_rate_limit" label={t('settings.rateLimit')}>
            <Input />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit">{t('common.save')}</Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
