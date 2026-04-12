import React, { useState, useEffect } from 'react';
import {
    CogIcon,
    WifiIcon,
    CurrencyDollarIcon,
    ShieldCheckIcon,
    BellIcon,
    ChartBarIcon,
    ServerIcon,
    DocumentTextIcon,
    CheckIcon,
    XMarkIcon,
} from '@heroicons/react/24/outline';
import { updateSettings, getSettings } from '../services/api';

const SettingsPage = () => {
    const [settings, setSettings] = useState({});
    const [loading, setLoading] = useState(false);
    const [saveStatus, setSaveStatus] = useState('');

    useEffect(() => {
        loadSettings();
    }, []);

    const loadSettings = async () => {
        try {
            setLoading(true);
            const response = await getSettings();
            setSettings(response.data);
        } catch (error) {
            console.error('Error loading settings:', error);
        } finally {
            setLoading(false);
        }
    };

    const saveSettings = async () => {
        try {
            setLoading(true);
            setSaveStatus('saving');
            const response = await updateSettings(settings);
            if (response.status === 200) {
                setSaveStatus('saved');
                setTimeout(() => setSaveStatus(''), 3000);
            } else {
                throw Error(response.statusText);
            }
        } catch (error) {
            console.error('Error saving settings:', error);
            setSaveStatus('error');
        } finally {
            setLoading(false);
        }
    };

    const handleSettingChange = (key: string, value: any) => {
        setSettings((prev) => ({ ...prev, [key]: value }));
    };

    const toggleSetting = (key: string) => {
        setSettings((prev) => ({ ...prev, [key]: !prev[key] }));
    };

    // Styled Components
    const SettingSection = ({ title, icon: Icon, children }) => (
        <div className="rounded-xl bg-white dark:bg-neo-dark/60 backdrop-blur-sm border border-gray-200 dark:border-neo-primary/20 p-5 shadow-md dark:shadow-lg transition-all duration-300">
            <div className="flex items-center gap-3 pb-4 mb-4 border-b border-gray-200 dark:border-neo-primary/20">
                <div className="p-2 rounded-lg bg-neo-primary/10 border border-neo-primary/30">
                    <Icon className="w-5 h-5 text-neo-primary" />
                </div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-neo-text">{title}</h2>
            </div>
            <div className="space-y-1">{children}</div>
        </div>
    );

    const ToggleSetting = ({ label, description, value, onChange, disabled = false }) => (
        <div className="flex items-center justify-between py-3">
            <div className="flex-1 pr-4">
                <label className="block text-sm font-medium text-gray-900 dark:text-neo-text mb-0.5">
                    {label}
                </label>
                <p className="text-xs text-gray-500 dark:text-neo-dim">{description}</p>
            </div>
            <button
                onClick={() => onChange(!value)}
                disabled={disabled}
                className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${value ? 'bg-neo-primary' : 'bg-gray-300 dark:bg-primary-800'
                    } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
                <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${value ? 'translate-x-5' : 'translate-x-0'
                        }`}
                />
            </button>
        </div>
    );

    const InputSetting = ({ label, description, type = 'text', value, onChange, unit, min, max }) => (
        <div className="py-3">
            <label className="block text-sm font-medium text-gray-900 dark:text-neo-text mb-0.5">
                {label}
            </label>
            <p className="text-xs text-gray-500 dark:text-neo-dim mb-2">{description}</p>
            <div className="flex items-center gap-3">
                <input
                    type={type}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    min={min}
                    max={max}
                    className="flex-1 px-4 py-2 rounded-lg bg-gray-50 dark:bg-primary-950/50 border border-gray-200 dark:border-neo-primary/20 text-gray-900 dark:text-neo-text placeholder-gray-400 dark:placeholder-neo-dim/50 focus:border-neo-primary focus:ring-1 focus:ring-neo-primary/30 outline-none transition-colors"
                />
                {unit && <span className="text-sm text-gray-500 dark:text-neo-dim w-12">{unit}</span>}
            </div>
        </div>
    );

    const SelectSetting = ({ label, description, value, onChange, options }) => (
        <div className="py-3">
            <label className="block text-sm font-medium text-gray-900 dark:text-neo-text mb-0.5">
                {label}
            </label>
            <p className="text-xs text-gray-500 dark:text-neo-dim mb-2">{description}</p>
            <select
                value={value}
                onChange={(e) => onChange(e.target.value)}
                className="w-full px-4 py-2 rounded-lg bg-gray-50 dark:bg-primary-950/50 border border-gray-200 dark:border-neo-primary/20 text-gray-900 dark:text-neo-text focus:border-neo-primary focus:ring-1 focus:ring-neo-primary/30 outline-none transition-colors"
            >
                {options.map((option) => (
                    <option key={option.value} value={option.value}>
                        {option.label}
                    </option>
                ))}
            </select>
        </div>
    );

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 dark:from-neo-darker dark:to-neo-dark transition-colors duration-300 p-4 sm:p-6">
            {/* Ambient background glows */}
            <div className="fixed inset-0 pointer-events-none">
                <div className="absolute -top-40 -right-40 h-96 w-96 rounded-full bg-neo-primary/5 blur-3xl" />
                <div className="absolute bottom-0 left-0 h-80 w-80 rounded-full bg-neo-secondary/5 blur-3xl" />
            </div>

            <div className="relative max-w-4xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center gap-3">
                    <div className="p-3 rounded-xl bg-neo-primary/10 border border-neo-primary/30">
                        <CogIcon className="w-6 h-6 text-neo-primary" />
                    </div>
                    <div>
                        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
                            <span className="bg-gradient-to-r from-neo-primary via-neo-secondary to-neo-accent bg-clip-text text-transparent">
                                System
                            </span>
                            <span className="text-gray-900 dark:text-neo-text"> Settings</span>
                        </h1>
                        <p className="text-gray-500 dark:text-neo-dim text-sm sm:text-base mt-1">
                            Configure your network and system preferences
                        </p>
                    </div>
                </div>

                {loading && !saveStatus ? (
                    <div className="flex justify-center py-12">
                        <div className="animate-spin rounded-full h-10 w-10 border-2 border-neo-primary border-t-transparent" />
                    </div>
                ) : (
                    <div className="space-y-5">
                        {/* Network Settings */}
                        <SettingSection title="Network Configuration" icon={WifiIcon}>
                            <InputSetting
                                label="Network Name"
                                description="Display name for your network"
                                value={settings.network_name}
                                onChange={(value) => handleSettingChange('network_name', value)}
                            />
                            <InputSetting
                                label="Max Devices Per User"
                                description="Maximum number of devices a single user can connect"
                                type="number"
                                value={settings.max_devices_per_user}
                                onChange={(value) => handleSettingChange('max_devices_per_user', parseInt(value))}
                                min="1"
                                max="20"
                            />
                            <InputSetting
                                label="Session Timeout"
                                description="Hours before requiring re-authentication"
                                type="number"
                                value={settings.session_timeout}
                                onChange={(value) => handleSettingChange('session_timeout', parseInt(value))}
                                unit="hours"
                                min="1"
                                max="720"
                            />
                            <InputSetting
                                label="Bandwidth Limit"
                                description="Monthly data limit per user"
                                type="number"
                                value={settings.bandwidth_limit}
                                onChange={(value) => handleSettingChange('bandwidth_limit', parseInt(value))}
                                unit="MB"
                                min="100"
                                max="10000"
                            />
                            <ToggleSetting
                                label="Guest Network"
                                description="Allow guest access without authentication"
                                value={settings.allow_guest_network}
                                onChange={(value) => handleSettingChange('allow_guest_network', value)}
                            />
                        </SettingSection>

                        {/* Payment Settings */}
                        <SettingSection title="Payment & Monetization" icon={CurrencyDollarIcon}>
                            <ToggleSetting
                                label="Free Internet Mode"
                                description="Provide free internet access to all users"
                                value={settings.free_internet_enabled}
                                onChange={(value) => handleSettingChange('free_internet_enabled', value)}
                            />
                            {!settings.free_internet_enabled && (
                                <>
                                    <ToggleSetting
                                        label="Paid Mode"
                                        description="Enable payment collection for internet access"
                                        value={settings.paid_mode_enabled}
                                        onChange={(value) => handleSettingChange('paid_mode_enabled', value)}
                                    />
                                    {settings.paid_mode_enabled && (
                                        <>
                                            <SelectSetting
                                                label="Payment Gateway"
                                                description="Choose your payment processing service"
                                                value={settings.payment_gateway}
                                                onChange={(value) => handleSettingChange('payment_gateway', value)}
                                                options={[
                                                    { value: 'mpesa', label: 'M-Pesa' },
                                                    { value: 'stripe', label: 'Stripe' },
                                                    { value: 'paypal', label: 'PayPal' },
                                                    { value: 'razorpay', label: 'Razorpay' },
                                                    { value: 'manual', label: 'Manual Payment' },
                                                ]}
                                            />
                                            <SelectSetting
                                                label="Currency"
                                                description="Default currency for payments"
                                                value={settings.currency}
                                                onChange={(value) => handleSettingChange('currency', value)}
                                                options={[
                                                    { value: 'KSH', label: 'Kenya Shilling (Ksh.)' },
                                                    { value: 'USD', label: 'US Dollar ($)' },
                                                    { value: 'EUR', label: 'Euro (€)' },
                                                    { value: 'GBP', label: 'British Pound (£)' },
                                                    { value: 'INR', label: 'Indian Rupee (₹)' },
                                                ]}
                                            />
                                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
                                                <InputSetting
                                                    label="Hourly Rate"
                                                    description="Cost per hour"
                                                    type="number"
                                                    value={settings.hourly_rate}
                                                    onChange={(value) => handleSettingChange('hourly_rate', parseFloat(value))}
                                                    unit={settings.currency}
                                                    min="0"
                                                    step="0.01"
                                                />
                                                <InputSetting
                                                    label="Daily Rate"
                                                    description="Cost per day"
                                                    type="number"
                                                    value={settings.daily_rate}
                                                    onChange={(value) => handleSettingChange('daily_rate', parseFloat(value))}
                                                    unit={settings.currency}
                                                    min="0"
                                                    step="0.01"
                                                />
                                                <InputSetting
                                                    label="Monthly Rate"
                                                    description="Cost per month"
                                                    type="number"
                                                    value={settings.monthly_rate}
                                                    onChange={(value) => handleSettingChange('monthly_rate', parseFloat(value))}
                                                    unit={settings.currency}
                                                    min="0"
                                                    step="0.01"
                                                />
                                            </div>
                                        </>
                                    )}
                                </>
                            )}
                        </SettingSection>

                        {/* Security Settings */}
                        <SettingSection title="Security Settings" icon={ShieldCheckIcon}>
                            <ToggleSetting
                                label="Require Authentication"
                                description="Users must authenticate before accessing the network"
                                value={settings.require_authentication}
                                onChange={(value) => handleSettingChange('require_authentication', value)}
                            />
                            <ToggleSetting
                                label="Captive Portal"
                                description="Redirect users to login page before granting access"
                                value={settings.enable_captive_portal}
                                onChange={(value) => handleSettingChange('enable_captive_portal', value)}
                            />
                            <ToggleSetting
                                label="Block VPN Connections"
                                description="Prevent VPN usage on your network"
                                value={settings.block_vpn_connections}
                                onChange={(value) => handleSettingChange('block_vpn_connections', value)}
                            />
                            <ToggleSetting
                                label="MAC Address Filtering"
                                description="Only allow registered devices to connect"
                                value={settings.enable_mac_filtering}
                                onChange={(value) => handleSettingChange('enable_mac_filtering', value)}
                            />
                            <InputSetting
                                label="Log Retention"
                                description="How long to keep system logs"
                                type="number"
                                value={settings.log_retention_days}
                                onChange={(value) => handleSettingChange('log_retention_days', parseInt(value))}
                                unit="days"
                                min="1"
                                max="365"
                            />
                        </SettingSection>

                        {/* Notifications */}
                        <SettingSection title="Notifications" icon={BellIcon}>
                            <ToggleSetting
                                label="Email Notifications"
                                description="Send notifications via email"
                                value={settings.email_notifications}
                                onChange={(value) => handleSettingChange('email_notifications', value)}
                            />
                            <ToggleSetting
                                label="SMS Notifications"
                                description="Send notifications via SMS"
                                value={settings.sms_notifications}
                                onChange={(value) => handleSettingChange('sms_notifications', value)}
                            />
                            <ToggleSetting
                                label="Low Balance Alerts"
                                description="Notify users when their balance is low"
                                value={settings.low_balance_alerts}
                                onChange={(value) => handleSettingChange('low_balance_alerts', value)}
                            />
                            <ToggleSetting
                                label="Security Alerts"
                                description="Receive alerts for suspicious activities"
                                value={settings.security_alerts}
                                onChange={(value) => handleSettingChange('security_alerts', value)}
                            />
                            <ToggleSetting
                                label="Monthly Reports"
                                description="Send monthly usage reports to users"
                                value={settings.monthly_reports}
                                onChange={(value) => handleSettingChange('monthly_reports', value)}
                            />
                        </SettingSection>

                        {/* System */}
                        <SettingSection title="System Configuration" icon={ServerIcon}>
                            <ToggleSetting
                                label="Maintenance Mode"
                                description="Put the system in maintenance mode"
                                value={settings.maintenance_mode}
                                onChange={(value) => handleSettingChange('maintenance_mode', value)}
                            />
                            <ToggleSetting
                                label="Auto Backup"
                                description="Automatically backup system data"
                                value={settings.auto_backup}
                                onChange={(value) => handleSettingChange('auto_backup', value)}
                            />
                            {settings.auto_backup && (
                                <SelectSetting
                                    label="Backup Frequency"
                                    description="How often to perform automatic backups"
                                    value={settings.backup_frequency}
                                    onChange={(value) => handleSettingChange('backup_frequency', value)}
                                    options={[
                                        { value: 'hourly', label: 'Every Hour' },
                                        { value: 'daily', label: 'Daily' },
                                        { value: 'weekly', label: 'Weekly' },
                                        { value: 'monthly', label: 'Monthly' },
                                    ]}
                                />
                            )}
                            <ToggleSetting
                                label="System Logs"
                                description="Enable detailed system logging"
                                value={settings.system_logs}
                                onChange={(value) => handleSettingChange('system_logs', value)}
                            />
                            <ToggleSetting
                                label="Debug Mode"
                                description="Enable debug logging for troubleshooting"
                                value={settings.debug_mode}
                                onChange={(value) => handleSettingChange('debug_mode', value)}
                            />
                        </SettingSection>

                        {/* Save Actions */}
                        <div className="rounded-xl bg-white dark:bg-neo-dark/60 backdrop-blur-sm border border-gray-200 dark:border-neo-primary/20 p-5 shadow-md dark:shadow-lg">
                            <div className="flex flex-wrap items-center justify-between gap-4">
                                <div>
                                    <h3 className="text-base font-semibold text-gray-900 dark:text-neo-text">
                                        Save Changes
                                    </h3>
                                    <p className="text-xs text-gray-500 dark:text-neo-dim">
                                        Apply your configuration changes to the system
                                    </p>
                                </div>
                                <div className="flex items-center gap-4">
                                    {saveStatus && (
                                        <span
                                            className={`flex items-center gap-1.5 text-sm ${saveStatus === 'saved'
                                                    ? 'text-neo-primary'
                                                    : saveStatus === 'error'
                                                        ? 'text-red-500'
                                                        : 'text-neo-dim'
                                                }`}
                                        >
                                            {saveStatus === 'saved' && <CheckIcon className="w-4 h-4" />}
                                            {saveStatus === 'error' && <XMarkIcon className="w-4 h-4" />}
                                            <span>
                                                {saveStatus === 'saving' && 'Saving...'}
                                                {saveStatus === 'saved' && 'Saved!'}
                                                {saveStatus === 'error' && 'Failed'}
                                            </span>
                                        </span>
                                    )}
                                    <button
                                        onClick={saveSettings}
                                        disabled={loading}
                                        className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-neo-primary to-cyber-500 text-white dark:text-gray-900 font-medium shadow-md hover:shadow-neo transition-all duration-300 disabled:opacity-50"
                                    >
                                        {loading ? 'Saving...' : 'Save Settings'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default SettingsPage;
