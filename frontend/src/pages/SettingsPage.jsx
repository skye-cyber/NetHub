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
    XMarkIcon
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
            const response = await getSettings()
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
            const response = await updateSettings(settings)
            if (response.status === 200) {
                setSaveStatus('saved');
                setTimeout(() => setSaveStatus(''), 3000);
            } else {
                throw Error(response.statusText)
            }

        } catch (error) {
            console.error('Error saving settings:', error);
            setSaveStatus('error');
        } finally {
            setLoading(false);
        }
    };

    const handleSettingChange = (key, value) => {
        setSettings(prev => ({
            ...prev,
            [key]: value
        }));
    };

    const toggleSetting = (key) => {
        setSettings(prev => ({
            ...prev,
            [key]: !prev[key]
        }));
    };

    const SettingSection = ({ title, icon: Icon, children }) => (
        <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl shadow-lg p-6 border border-white/20 dark:border-gray-700/50 mb-6">
            <div className="flex items-center space-x-3 mb-4 pb-4 border-b border-gray-200/50 dark:border-gray-600/50">
                <Icon className="w-6 h-6 text-blue-500" />
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">{title}</h2>
            </div>
            {children}
        </div>
    );

    const ToggleSetting = ({ label, description, value, onChange, disabled = false }) => (
        <div className="flex items-center justify-between py-3">
            <div className="flex-1">
                <label className="block text-sm font-medium text-gray-900 dark:text-white mb-1">
                    {label}
                </label>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                    {description}
                </p>
            </div>
            <button
                onClick={() => onChange(!value)}
                disabled={disabled}
                className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${value ? 'bg-green-500' : 'bg-gray-200 dark:bg-gray-600'
                    } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
                <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${value ? 'translate-x-5' : 'translate-x-0'
                        }`}
                />
            </button>
        </div>
    );

    const InputSetting = ({ label, description, type = "text", value, onChange, unit, min, max }) => (
        <div className="py-3">
            <label className="block text-sm font-medium text-gray-900 dark:text-white mb-1">
                {label}
            </label>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                {description}
            </p>
            <div className="flex space-x-3">
                <input
                    type={type}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    min={min}
                    max={max}
                    className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                {unit && <span className="flex items-center text-sm text-gray-500 dark:text-gray-400">{unit}</span>}
            </div>
        </div>
    );

    const SelectSetting = ({ label, description, value, onChange, options }) => (
        <div className="py-3">
            <label className="block text-sm font-medium text-gray-900 dark:text-white mb-1">
                {label}
            </label>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                {description}
            </p>
            <select
                value={value}
                onChange={(e) => onChange(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
                {options.map(option => (
                    <option key={option.value} value={option.value}>
                        {option.label}
                    </option>
                ))}
            </select>
        </div>
    );

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-cyan-50 dark:from-gray-900 dark:via-purple-900/20 dark:to-blue-900/20 p-4">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <div className="flex items-center space-x-3 mb-2">
                        <CogIcon className="w-8 h-8 text-blue-500" />
                        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                            System Settings
                        </h1>
                    </div>
                    <p className="text-gray-600 dark:text-gray-300">
                        Configure your network and system preferences
                    </p>
                </div>

                {loading && !saveStatus ? (
                    <div className="flex justify-center items-center py-12">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                    </div>
                ) : (
                    <>
                        {/* Network Settings */}
                        <SettingSection title="Network Configuration" icon={WifiIcon}>
                            <div className="space-y-2">
                                {/*<SelectSetting
                                    label="Seletc Network"
                                    description="Network to configure"
                                    options={[]}
                                    value={settings.network_name}
                                    onChange={(value) => handleSettingChange('network_name', value)}
                                />*/
                                }

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
                            </div>
                        </SettingSection>

                        {/* Payment & Monetization */}
                        <SettingSection title="Payment & Monetization" icon={CurrencyDollarIcon}>
                            <div className="space-y-2">
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
                                                        { value: 'stripe', label: 'Stripe' },
                                                        { value: 'paypal', label: 'PayPal' },
                                                        { value: 'razorpay', label: 'Razorpay' },
                                                        { value: 'manual', label: 'Manual Payment' }
                                                    ]}
                                                />
                                                <SelectSetting
                                                    label="Currency"
                                                    description="Default currency for payments"
                                                    value={settings.currency}
                                                    onChange={(value) => handleSettingChange('currency', value)}
                                                    options={[
                                                        { value: 'USD', label: 'US Dollar ($)' },
                                                        { value: 'EUR', label: 'Euro (€)' },
                                                        { value: 'GBP', label: 'British Pound (£)' },
                                                        { value: 'INR', label: 'Indian Rupee (₹)' }
                                                    ]}
                                                />
                                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
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
                            </div>
                        </SettingSection>

                        {/* Security Settings */}
                        <SettingSection title="Security Settings" icon={ShieldCheckIcon}>
                            <div className="space-y-2">
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
                            </div>
                        </SettingSection>

                        {/* Notification Settings */}
                        <SettingSection title="Notifications" icon={BellIcon}>
                            <div className="space-y-2">
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
                            </div>
                        </SettingSection>

                        {/* System Settings */}
                        <SettingSection title="System Configuration" icon={ServerIcon}>
                            <div className="space-y-2">
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
                                            { value: 'monthly', label: 'Monthly' }
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
                            </div>
                        </SettingSection>

                        {/* Save Actions */}
                        <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl shadow-lg p-6 border border-white/20 dark:border-gray-700/50">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                                        Save Changes
                                    </h3>
                                    <p className="text-sm text-gray-600 dark:text-gray-400">
                                        Apply your configuration changes to the system
                                    </p>
                                </div>
                                <div className="flex items-center space-x-4">
                                    {saveStatus && (
                                        <span className={`flex items-center space-x-2 text-sm ${saveStatus === 'saved' ? 'text-green-600 dark:text-green-400' :
                                            saveStatus === 'error' ? 'text-red-600 dark:text-red-400' :
                                                'text-blue-600 dark:text-blue-400'
                                            }`}>
                                            {saveStatus === 'saved' && <CheckIcon className="w-4 h-4" />}
                                            {saveStatus === 'error' && <XMarkIcon className="w-4 h-4" />}
                                            <span>
                                                {saveStatus === 'saving' && 'Saving...'}
                                                {saveStatus === 'saved' && 'Changes Saved!'}
                                                {saveStatus === 'error' && 'Save Failed'}
                                            </span>
                                        </span>
                                    )}
                                    <button
                                        onClick={saveSettings}
                                        disabled={loading}
                                        className="bg-gradient-to-r from-blue-600 to-cyan-600 text-white px-6 py-3 rounded-lg font-medium hover:from-blue-700 hover:to-cyan-700 disabled:opacity-50 transition-all duration-300 shadow-lg hover:shadow-xl"
                                    >
                                        {loading ? 'Saving...' : 'Save Settings'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default SettingsPage;
