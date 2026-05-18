import { useEffect, useState } from 'react';
import { Card, Form, Input, Select, Button, InputNumber, Switch, Radio, Checkbox, message, Space, Divider, Typography, Collapse, Popconfirm } from 'antd';
import { ApiOutlined } from '@ant-design/icons';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { guardrailsApi } from '../../../api/guardrails';

const { TextArea } = Input;
const { Option } = Select;
const { Text } = Typography;

const GUARDRAIL_TYPES_BY_DOMAIN: Record<string, string[]> = {
  llm: ['privacy', 'compliance', 'injection', 'sensitive', 'pii', 'jailbreak', 'custom'],
  mcp: ['param_validation', 'tool_whitelist', 'tool_blacklist', 'rate_check', 'custom'],
  memory: ['write_check', 'read_desensitize', 'custom'],
};

export default function GuardrailForm() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const basePath = location.pathname.startsWith('/admin') ? '/admin' : '/user';
  const { id } = useParams();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [domain, setDomain] = useState('llm');
  const [action, setAction] = useState('block');
  const [testResult, setTestResult] = useState<any>(null);
  const isEdit = !!id;

  useEffect(() => {
    if (isEdit) {
      guardrailsApi.get(id!).then((res) => {
        const d = res.data.data;
        form.setFieldsValue(d);
        setDomain(d.domain);
        setAction(d.hit_action);
      });
    }
  }, [id]);

  const onFinish = async (values: any) => {
    setLoading(true);
    try {
      if (isEdit) {
        await guardrailsApi.update(id!, values);
        message.success(t('common.updateSuccess'));
      } else {
        await guardrailsApi.create(values);
        message.success(t('common.createSuccess'));
      }
      navigate(`${basePath}/guardrails`);
    } catch (err: any) {
      message.error(err.response?.data?.detail || t('common.saveFailed'));
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async () => {
    if (isEdit) {
      const testMessages = [{ role: 'user', content: 'Test message for guardrail' }];
      const res = await guardrailsApi.test(id!, { messages: testMessages });
      setTestResult(res.data.data);
    }
  };

  const handleDelete = async () => {
    await guardrailsApi.delete(id!);
    message.success(t('common.deleteSuccess'));
    navigate(`${basePath}/guardrails`);
  };

  return (
    <div>
      <h2 className="page-header">{isEdit ? t('common.edit') : t('common.create')} {t('nav.guardrails')}</h2>
      <Card>
        <Form form={form} layout="vertical" onFinish={onFinish}
          initialValues={{
            domain: 'llm', position: 'pre', hit_action: 'block',
            default_priority: 50, timeout_ms: 3000, retry_count: 0,
            enabled: true, supports_multimodal: false, streaming_enabled: false,
          }}>
          <Divider orientation="left">{t('common.basicConfig')}</Divider>
          <Form.Item name="name" label={t('guardrails.name')} rules={[{ required: true, max: 50 }]}>
            <Input />
          </Form.Item>
          <Form.Item name="domain" label={t('guardrails.domain')} rules={[{ required: true }]}>
            <Select onChange={(v) => { setDomain(v); form.setFieldValue('guardrail_type', undefined); }}>
              <Option value="llm">LLM</Option>
              <Option value="mcp">MCP</Option>
              <Option value="memory">Memory</Option>
            </Select>
          </Form.Item>
          <Form.Item name="guardrail_type" label={t('guardrails.type')} rules={[{ required: true }]}>
            <Select>
              {(GUARDRAIL_TYPES_BY_DOMAIN[domain] || []).map((t) => (
                <Option key={t} value={t}>{t}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="position" label={t('guardrails.position')} rules={[{ required: true }]}>
            <Select>
              <Option value="pre">{t('guardrails.pre')}</Option>
              <Option value="post">{t('guardrails.post')}</Option>
            </Select>
          </Form.Item>
          <Form.Item name="description" label={t('guardrails.description')} rules={[{ required: true, max: 200 }]}>
            <TextArea rows={2} maxLength={200} />
          </Form.Item>
          <Form.Item name="default_priority" label={t('guardrails.priority')}>
            <InputNumber min={1} max={100} />
          </Form.Item>

          <Divider orientation="left">{t('guardrails.httpConfig')}</Divider>
          <Form.Item name="endpoint_url" label={t('guardrails.endpointUrl')} rules={[{ required: true }]}>
            <Input placeholder="https://guardrail.example.com/v1/detect" />
          </Form.Item>
          <Form.Item name="timeout_ms" label={t('guardrails.timeout')}>
            <InputNumber min={100} max={30000} style={{ width: '100%' }} addonAfter="ms" />
          </Form.Item>
          <Form.Item name="retry_count" label={t('guardrails.retryCount')}>
            <InputNumber min={0} max={5} />
          </Form.Item>
          <Form.Item name="supports_multimodal" label={t('guardrails.multimodal')} valuePropName="checked">
            <Switch />
          </Form.Item>

          <Divider orientation="left">{t('guardrails.streamingConfig')}</Divider>
          <Form.Item name="streaming_enabled" label={t('guardrails.streamingEnabled')} valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="window_tokens" label={t('guardrails.windowTokens')}>
            <InputNumber min={10} max={10000} />
          </Form.Item>

          <Divider orientation="left">{t('guardrails.hitAction')}</Divider>
          <Form.Item name="hit_action" label={t('guardrails.hitAction')}>
            <Radio.Group onChange={(e) => setAction(e.target.value)}>
              <Radio value="alert">{t('guardrails.alert')}</Radio>
              <Radio value="block">{t('guardrails.block')}</Radio>
              <Radio value="correct">{t('guardrails.correct')}</Radio>
            </Radio.Group>
          </Form.Item>

          <Divider orientation="left">{t('common.status')}</Divider>
          <Form.Item name="enabled" label={t('guardrails.enabled')} valuePropName="checked">
            <Switch />
          </Form.Item>

          {isEdit && (
            <Collapse style={{ marginTop: 16 }} items={[{
              key: 'test', label: t('guardrails.testPanel'),
              children: (
                <Space direction="vertical">
                  <Button icon={<ApiOutlined />} onClick={handleTest}>{t('common.test')}</Button>
                  {testResult && (
                    <pre style={{ background: '#f5f5f5', padding: 12, borderRadius: 6, maxHeight: 300, overflow: 'auto' }}>
                      {JSON.stringify(testResult, null, 2)}
                    </pre>
                  )}
                </Space>
              ),
            }]} />
          )}

          <Divider />
          <Space>
            <Button type="primary" onClick={() => form.submit()} loading={loading}>{t('common.save')}</Button>
            <Button onClick={() => navigate(`${basePath}/guardrails`)}>{t('common.cancel')}</Button>
            {isEdit && (
              <Popconfirm title={t('common.confirmDelete')} onConfirm={handleDelete}>
                <Button danger>{t('common.delete')}</Button>
              </Popconfirm>
            )}
          </Space>
        </Form>
      </Card>
    </div>
  );
}
