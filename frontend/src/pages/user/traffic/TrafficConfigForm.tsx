import { useEffect, useState } from 'react';
import { Card, Form, Input, Button, Switch, Select, message, Space, Divider, Tag } from 'antd';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { trafficApi } from '../../../api/traffic';
import { assetsApi } from '../../../api/assets';
import { guardrailsApi } from '../../../api/guardrails';
import type { Asset, Guardrail } from '../../../types';

export default function TrafficConfigForm() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const basePath = location.pathname.startsWith('/admin') ? '/admin' : '/user';
  const { id } = useParams();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [guardrails, setGuardrails] = useState<Guardrail[]>([]);
  const [selectedAssets, setSelectedAssets] = useState<string[]>([]);
  const [preEntries, setPreEntries] = useState<{ guardrailId: string; priority: number }[]>([]);
  const [postEntries, setPostEntries] = useState<{ guardrailId: string; priority: number }[]>([]);
  const isEdit = !!id;

  useEffect(() => {
    assetsApi.list({ page_size: 100 }).then((res) => setAssets(res.data.data.items));
    guardrailsApi.list({ page_size: 100 }).then((res) => setGuardrails(res.data.data.items));
    if (isEdit) {
      trafficApi.get(id!).then((res) => {
        const d = res.data.data;
        form.setFieldsValue(d);
        setSelectedAssets(d.asset_ids || []);
        setPreEntries(d.guardrail_entries?.filter((e: any) => e.position === 'pre') || []);
        setPostEntries(d.guardrail_entries?.filter((e: any) => e.position === 'post') || []);
      });
    }
  }, [id]);

  const onFinish = async (values: any) => {
    setLoading(true);
    try {
      const payload = {
        ...values,
        asset_ids: selectedAssets,
        guardrail_entries: [
          ...preEntries.map((e, i) => ({ guardrail_id: e.guardrailId, position: 'pre', priority: e.priority || i + 1 })),
          ...postEntries.map((e, i) => ({ guardrail_id: e.guardrailId, position: 'post', priority: e.priority || i + 1 })),
        ],
      };
      if (isEdit) {
        await trafficApi.update(id!, payload);
        message.success(t('common.updateSuccess'));
      } else {
        await trafficApi.create(payload);
        message.success(t('common.createSuccess'));
      }
      navigate(`${basePath}/traffic-configs`);
    } catch (err: any) {
      message.error(err.response?.data?.detail || t('common.saveFailed'));
    } finally { setLoading(false); }
  };

  const getGuardrailName = (gid: string) => guardrails.find((g) => g.id === gid)?.name || gid;

  return (
    <div>
      <h2 className="page-header">{isEdit ? t('common.edit') : t('common.create')} {t('nav.trafficConfigs')}</h2>
      <Card>
        <Form form={form} layout="vertical" onFinish={onFinish} initialValues={{ enabled: true, execution_mode: 'serial' }}>
          <Form.Item name="name" label={t('traffic.name')} rules={[{ required: true, max: 50 }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label={t('traffic.description')}>
            <Input.TextArea rows={2} maxLength={200} />
          </Form.Item>
          <Form.Item name="execution_mode" label={t('traffic.executionMode')}>
            <Select>
              <Select.Option value="serial">{t('traffic.serial')}</Select.Option>
              <Select.Option value="parallel">{t('traffic.parallel')}</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="enabled" label={t('common.enabled')} valuePropName="checked">
            <Switch />
          </Form.Item>

          <Divider orientation="left">{t('traffic.linkAssets')}</Divider>
          <Select
            mode="multiple"
            style={{ width: '100%' }}
            value={selectedAssets}
            onChange={setSelectedAssets}
            placeholder={t('common.select')}
            options={assets.map((a) => ({ label: `${a.name} (${a.type})`, value: a.id }))}
          />

          <Divider orientation="left">{t('guardrails.pre')} {t('nav.guardrails')}</Divider>
          <Select
            mode="multiple"
            style={{ width: '100%' }}
            value={preEntries.map((e) => e.guardrailId)}
            onChange={(ids) => setPreEntries(ids.map((gid, i) => ({ guardrailId: gid, priority: i + 1 })))}
            placeholder={t('common.select')}
            options={guardrails.filter((g) => g.position === 'pre').map((g) => ({ label: g.name, value: g.id }))}
          />
          <div style={{ marginTop: 8 }}>
            {preEntries.map((e) => (
              <Tag key={e.guardrailId} closable onClose={() => setPreEntries(preEntries.filter((x) => x.guardrailId !== e.guardrailId))}>
                {getGuardrailName(e.guardrailId)} (P{e.priority})
              </Tag>
            ))}
          </div>

          <Divider orientation="left">{t('guardrails.post')} {t('nav.guardrails')}</Divider>
          <Select
            mode="multiple"
            style={{ width: '100%' }}
            value={postEntries.map((e) => e.guardrailId)}
            onChange={(ids) => setPostEntries(ids.map((gid, i) => ({ guardrailId: gid, priority: i + 1 })))}
            placeholder={t('common.select')}
            options={guardrails.filter((g) => g.position === 'post').map((g) => ({ label: g.name, value: g.id }))}
          />
          <div style={{ marginTop: 8 }}>
            {postEntries.map((e) => (
              <Tag key={e.guardrailId} closable onClose={() => setPostEntries(postEntries.filter((x) => x.guardrailId !== e.guardrailId))}>
                {getGuardrailName(e.guardrailId)} (P{e.priority})
              </Tag>
            ))}
          </div>

          <Divider />
          <Space>
            <Button type="primary" onClick={() => form.submit()} loading={loading}>{t('common.save')}</Button>
            <Button onClick={() => navigate(`${basePath}/traffic-configs`)}>{t('common.cancel')}</Button>
          </Space>
        </Form>
      </Card>
    </div>
  );
}
