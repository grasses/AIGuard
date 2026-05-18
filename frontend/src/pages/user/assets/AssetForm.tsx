import { useEffect, useState } from 'react';
import { Card, Form, Input, Select, Button, InputNumber, Switch, Radio, Slider, message, Space, Divider, Popconfirm } from 'antd';
import { useNavigate, useParams, useSearchParams, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { assetsApi } from '../../../api/assets';

const { TextArea } = Input;
const { Option } = Select;

export default function AssetForm() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const basePath = location.pathname.startsWith('/admin') ? '/admin' : '/user';
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);
  const isEdit = !!id;
  const assetType = searchParams.get('type') || 'llm';

  useEffect(() => {
    if (isEdit) {
      assetsApi.get(id!).then((res) => form.setFieldsValue(res.data.data));
    }
  }, [id]);

  const onFinish = async (values: any) => {
    setLoading(true);
    try {
      if (isEdit) {
        await assetsApi.update(id!, values);
        message.success(t('common.updateSuccess'));
      } else {
        await assetsApi.create({ ...values, type: assetType });
        message.success(t('common.createSuccess'));
      }
      navigate(`${basePath}/assets?tab=${assetType}`);
    } catch (err: any) {
      message.error(err.response?.data?.detail || t('common.saveFailed'));
    } finally { setLoading(false); }
  };

  const handleTest = async () => {
    if (isEdit) {
      const res = await assetsApi.test(id!);
      setTestResult(res.data.data);
    }
  };

  const handleDelete = async () => {
    if (isEdit) {
      await assetsApi.delete(id!);
      message.success(t('common.deleteSuccess'));
      navigate(`${basePath}/assets?tab=${assetType}`);
    }
  };

  return (
    <div>
      <h2 className="page-header">{isEdit ? t('common.edit') : t('common.create')} - {t('assets.' + assetType)}</h2>
      <Card>
        <Form form={form} layout="vertical" onFinish={onFinish} initialValues={{
          enabled: true, visibility: 'private', temperature: 0.7, max_tokens: 4096,
          timeout_seconds: 60, max_retries: 3
        }}>
          <Divider orientation="left">{t('common.basicConfig')}</Divider>
          <Form.Item name="name" label={t('assets.name')} rules={[{ required: true, max: 50 }]}>
            <Input />
          </Form.Item>

          {assetType === 'llm' && (<>
            <Form.Item name="provider" label={t('assets.provider')} rules={[{ required: true }]}>
              <Select><Option value="OpenAI">OpenAI</Option><Option value="Azure">Azure</Option>
                <Option value="Anthropic">Anthropic</Option><Option value="DeepSeek">DeepSeek</Option>
                <Option value="custom">{t('common.custom')}</Option></Select>
            </Form.Item>
            <Form.Item name="protocol" label={t('assets.protocol')}><Input placeholder="openai" /></Form.Item>
            <Form.Item name="base_url" label={t('assets.baseUrl')} rules={[{ required: true }]}>
              <Input placeholder="https://api.openai.com/v1" /></Form.Item>
            <Form.Item name="api_key" label={t('assets.apiKey')} rules={[{ required: true }]}>
              <Input.Password /></Form.Item>
            <Form.Item name="model_names" label={t('assets.modelNames')} rules={[{ required: true }]}>
              <Select mode="tags" placeholder={t('assets.modelNamesPlaceholder')} /></Form.Item>
          </>)}

          {assetType === 'mcp' && (<>
            <Form.Item name="tool_name" label={t('assets.toolName')} rules={[{ required: true, max: 50 }]}><Input /></Form.Item>
            <Form.Item name="description" label={t('assets.description')} rules={[{ required: true, max: 500 }]}><TextArea rows={3} /></Form.Item>
            <Form.Item name="endpoint_url" label={t('assets.endpointUrl')} rules={[{ required: true }]}><Input /></Form.Item>
            <Form.Item name="method" label={t('assets.method')} rules={[{ required: true }]}>
              <Select><Option value="GET">GET</Option><Option value="POST">POST</Option>
                <Option value="PUT">PUT</Option><Option value="DELETE">DELETE</Option></Select></Form.Item>
            <Form.Item name="authentication_type" label={t('assets.authType')}>
              <Select><Option value="none">{t('common.none')}</Option>
                <Option value="bearer">Bearer Token</Option><Option value="api_key">API Key</Option></Select></Form.Item>
          </>)}

          {assetType === 'memory' && (<>
            <Form.Item name="index_name" label={t('assets.indexName')} rules={[{ required: true }]}><Input /></Form.Item>
            <Form.Item name="max_tokens_capacity" label={t('assets.maxTokensCapacity')} rules={[{ required: true }]}>
              <InputNumber min={1} style={{ width: '100%' }} /></Form.Item>
            <Form.Item name="persist" label={t('assets.persist')} valuePropName="checked"><Switch /></Form.Item>
            <Form.Item name="expire_days" label={t('assets.expireDays')}><InputNumber min={0} style={{ width: '100%' }} /></Form.Item>
          </>)}

          {assetType === 'llm' && (<>
            <Divider orientation="left">{t('common.advancedConfig')}</Divider>
            <Form.Item name="max_tokens" label={t('assets.maxTokens')}><InputNumber min={1} style={{ width: '100%' }} /></Form.Item>
            <Form.Item name="timeout_seconds" label={t('assets.timeout')}><InputNumber min={1} style={{ width: '100%' }} /></Form.Item>
            <Form.Item name="max_retries" label={t('assets.maxRetries')}><InputNumber min={0} style={{ width: '100%' }} /></Form.Item>
            <Form.Item name="temperature" label={t('assets.temperature')}>
              <Slider min={0} max={2} step={0.1} marks={{ 0: '0', 1: '1', 2: '2' }} /></Form.Item>
          </>)}

          <Divider orientation="left">{t('common.visibility')}</Divider>
          <Form.Item name="visibility" label={t('assets.visibility')}>
            <Radio.Group><Radio value="private">{t('assets.private')}</Radio>
              <Radio value="group">{t('assets.group')}</Radio><Radio value="public">{t('assets.public')}</Radio></Radio.Group></Form.Item>
          <Form.Item name="notes" label={t('assets.notes')}><TextArea rows={2} maxLength={200} /></Form.Item>

          {isEdit && (<>
            <Divider orientation="left">{t('common.connectivityTest')}</Divider>
            <Space><Button onClick={handleTest}>{t('common.testConnection')}</Button>
              {testResult && <span style={{ color: testResult.success ? 'green' : 'red' }}>
                {testResult.success ? `OK — ${testResult.latency_ms}ms` : testResult.message}</span>}</Space>
          </>)}

          <Divider orientation="left">{t('common.status')}</Divider>
          <Form.Item name="enabled" label={t('assets.enabled')} valuePropName="checked"><Switch /></Form.Item>

          <Divider />
          <Space>
            <Button type="primary" onClick={() => form.submit()} loading={loading}>{t('common.save')}</Button>
            <Button onClick={() => navigate(`${basePath}/assets?tab=${assetType}`)}>{t('common.cancel')}</Button>
            {isEdit && <Popconfirm title={t('common.confirmDelete')} onConfirm={handleDelete}>
              <Button danger>{t('common.delete')}</Button></Popconfirm>}
          </Space>
        </Form>
      </Card>
    </div>
  );
}
