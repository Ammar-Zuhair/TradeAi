import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  Keyboard,
  TouchableWithoutFeedback,
  TouchableOpacity,
  TextInput,
  Alert,
  KeyboardAvoidingView,
  Platform,
  BackHandler,
  Modal,
  FlatList,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { Server, Globe, User, Lock, CheckCircle, CreditCard, DollarSign, Hash } from 'lucide-react-native';
import Animated, { FadeInDown } from 'react-native-reanimated';

import { useAccounts } from '@/contexts/AccountsContext';
import { useTheme } from '@/contexts/ThemeContext';
import Layout from '@/constants/Layout';
import { HeadingText, BodyText } from '@/components/StyledText';
import Input from '@/components/Input';
import { brokerService } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import Button from '@/components/Button';

export default function AddAccountScreen() {
  const { addAccount, error, clearError } = useAccounts();
  const { user } = useAuth();
  const { colors } = useTheme();

  const [formData, setFormData] = useState({
    accountName: '',
    loginNumber: '',
    password: '',
    server: '',
    serverId: undefined as number | undefined,
    riskPercentage: '1.00',
    strategy: 'All' as 'All' | 'FVG + Trend' | 'Voting',
  });

  // Broker & Server Selection State
  const [brokers, setBrokers] = useState<any[]>([]);
  const [servers, setServers] = useState<any[]>([]);
  const [selectedBroker, setSelectedBroker] = useState<{ id: number; name: string } | null>(null);

  const [isBrokerModalOpen, setIsBrokerModalOpen] = useState(false);
  const [isServerModalOpen, setIsServerModalOpen] = useState(false);
  const [brokerSearch, setBrokerSearch] = useState('');
  const [isSearchingBrokers, setIsSearchingBrokers] = useState(false);

  const [isLoading, setIsLoading] = useState(false);

  // Handle back button press
  useEffect(() => {
    const backAction = () => {
      Alert.alert(
        'Exit App',
        'Are you sure you want to exit?',
        [
          {
            text: 'Cancel',
            onPress: () => null,
            style: 'cancel'
          },
          {
            text: 'Exit',
            onPress: () => BackHandler.exitApp()
          }
        ]
      );
      return true;
    };

    const backHandler = BackHandler.addEventListener(
      'hardwareBackPress',
      backAction
    );

    return () => backHandler.remove();
  }, []);

  // Search Brokers Effect
  useEffect(() => {
    const searchBrokers = async () => {
      if (!user?.token) return;
      setIsSearchingBrokers(true);
      try {
        const results = await brokerService.searchBrokers(user.token, brokerSearch);
        setBrokers(results);
      } catch (err) {
        console.log('Error searching brokers:', err);
      } finally {
        setIsSearchingBrokers(false);
      }
    };

    const debounce = setTimeout(() => {
      searchBrokers();
    }, 500);

    return () => clearTimeout(debounce);
  }, [brokerSearch, user?.token]);

  const handleSelectBroker = async (broker: any) => {
    setSelectedBroker({ id: broker.broker_id, name: broker.broker_name });
    setIsBrokerModalOpen(false);
    setFormData(prev => ({ ...prev, server: '', serverId: undefined })); // Reset server

    // Fetch Servers for this broker
    if (user?.token) {
      try {
        const serverResults = await brokerService.getBrokerServers(user.token, broker.broker_id);
        setServers(serverResults);
      } catch (err) {
        console.log('Error fetching servers:', err);
        Alert.alert('Error', 'Failed to fetch servers for this broker');
      }
    }
  };

  const handleSelectServer = (server: any) => {
    setFormData(prev => ({ ...prev, server: server.server_name, serverId: server.server_id }));
    setIsServerModalOpen(false);
  };

  const handleAddAccount = async () => {
    if (!formData.accountName || !formData.loginNumber || !formData.password || !formData.server) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }

    const riskValue = parseFloat(formData.riskPercentage);
    if (isNaN(riskValue) || riskValue < 0 || riskValue > 10) {
      Alert.alert('Error', 'Risk percentage must be between 0% and 10%');
      return;
    }

    setIsLoading(true);
    try {
      const result = await addAccount({
        accountName: formData.accountName,
        loginNumber: formData.loginNumber,
        password: formData.password,
        server: formData.server,
        serverId: formData.serverId,
        riskPercentage: riskValue,
        strategy: formData.strategy,
      });

      if (result.success) {
        Alert.alert(
          'Success!',
          `${result.message}\n\n` +
          `Balance: $${result.mt5Info?.balance || 0}\n` +
          `Leverage: 1:${result.mt5Info?.leverage || 0}\n` +
          `Server: ${result.mt5Info?.server || formData.server}`,
          [{ 
            text: 'OK', 
            onPress: () => {
              // Reset form
              setFormData({
                accountName: '',
                loginNumber: '',
                password: '',
                server: '',
                serverId: undefined,
                riskPercentage: '1.00',
                strategy: 'All',
              });
              setSelectedBroker(null);
              // router.back() // User requested to stay on screen to add more
            } 
          }]
        );
      } else {
        Alert.alert('Verification Failed', result.message);
      }
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to add account');
    } finally {
      setIsLoading(false);
    }
  };

  // Dynamic styles
  const themeStyles = {
    container: { backgroundColor: colors.surface },
    title: { color: colors.text },
    label: { color: colors.text },
    inputContainer: {
      backgroundColor: colors.card,
      borderColor: colors.border,
    },
    input: { color: colors.text },
    placeholder: colors.placeholder,
    icon: colors.placeholder,
    typeButton: {
      borderColor: colors.border,
      backgroundColor: colors.card,
    },
    typeButtonActive: {
      borderColor: colors.primary,
      backgroundColor: 'rgba(91, 72, 210, 0.1)',
    },
    typeText: { color: colors.placeholder },
    typeTextActive: { color: colors.primary },
    modalOverlay: {
      backgroundColor: 'rgba(0,0,0,0.5)',
    },
    modalContent: {
      backgroundColor: colors.surface,
      borderColor: colors.border,
    },
    listItem: {
      borderBottomColor: colors.border,
    },
    listText: {
      color: colors.text,
    }
  };

  const renderSelectionModal = (
    visible: boolean,
    onClose: () => void,
    title: string,
    isBroker: boolean
  ) => (
    <Modal
      visible={visible}
      transparent
      animationType="slide"
      onRequestClose={onClose}
    >
      <View style={[styles.modalOverlay, themeStyles.modalOverlay]}>
        <View style={[styles.modalContent, themeStyles.modalContent]}>
          <View style={styles.modalHeader}>
            <HeadingText style={[styles.modalTitle, themeStyles.title]}>{title}</HeadingText>
            <TouchableOpacity onPress={onClose}>
              <BodyText style={styles.closeButton}>Close</BodyText>
            </TouchableOpacity>
          </View>

          {isBroker && (
            <View style={[styles.inputContainer, themeStyles.inputContainer, { marginBottom: 10 }]}>
              <Globe size={20} color={themeStyles.icon} style={styles.inputIcon} />
              <TextInput
                style={[styles.input, themeStyles.input]}
                value={brokerSearch}
                onChangeText={setBrokerSearch}
                placeholder="Search broker..."
                placeholderTextColor={themeStyles.placeholder}
                autoFocus
              />
            </View>
          )}

          <FlatList
            data={isBroker ? brokers : servers}
            keyExtractor={(item) => (isBroker ? item.broker_id.toString() : item.server_id.toString())}
            renderItem={({ item }) => (
              <TouchableOpacity
                style={[styles.listItem, themeStyles.listItem]}
                onPress={() => isBroker ? handleSelectBroker(item) : handleSelectServer(item)}
              >
                <BodyText style={[styles.listText, themeStyles.listText]}>
                  {isBroker ? item.broker_name : item.server_name}
                </BodyText>
              </TouchableOpacity>
            )}
            ListEmptyComponent={
              <BodyText style={{ textAlign: 'center', marginTop: 20, color: themeStyles.placeholder }}>
                {isBroker
                  ? (isSearchingBrokers ? 'Searching...' : 'No brokers found')
                  : 'No servers available'}
              </BodyText>
            }
          />
        </View>
      </View>
    </Modal>
  );

  return (
    <SafeAreaView style={[styles.container, themeStyles.container]} edges={['top']}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          <View style={styles.header}>
            <HeadingText style={[styles.title, themeStyles.title]}>Add New Account</HeadingText>
          </View>

          <View style={styles.form}>
            {/* Account Name */}
            <View style={styles.inputGroup}>
              <BodyText style={[styles.label, themeStyles.label]}>Account Name *</BodyText>
              <View style={[styles.inputContainer, themeStyles.inputContainer]}>
                <User size={20} color={themeStyles.icon} style={styles.inputIcon} />
                <TextInput
                  style={[styles.input, themeStyles.input]}
                  value={formData.accountName}
                  onChangeText={(text) => setFormData({ ...formData, accountName: text })}
                  placeholder="e.g., My Trading Account"
                  placeholderTextColor={themeStyles.placeholder}
                />
              </View>
            </View>

            {/* Login Number */}
            <View style={styles.inputGroup}>
              <BodyText style={[styles.label, themeStyles.label]}>Login Number *</BodyText>
              <View style={[styles.inputContainer, themeStyles.inputContainer]}>
                <Hash size={20} color={themeStyles.icon} style={styles.inputIcon} />
                <TextInput
                  style={[styles.input, themeStyles.input]}
                  value={formData.loginNumber}
                  onChangeText={(text) => setFormData({ ...formData, loginNumber: text })}
                  placeholder="Account Login Number"
                  placeholderTextColor={themeStyles.placeholder}
                  keyboardType="numeric"
                />
              </View>
            </View>

            {/* Password */}
            <View style={styles.inputGroup}>
              <BodyText style={[styles.label, themeStyles.label]}>Password *</BodyText>
              <View style={[styles.inputContainer, themeStyles.inputContainer]}>
                <Lock size={20} color={themeStyles.icon} style={styles.inputIcon} />
                <TextInput
                  style={[styles.input, themeStyles.input]}
                  value={formData.password}
                  onChangeText={(text) => setFormData({ ...formData, password: text })}
                  placeholder="Account Password"
                  placeholderTextColor={themeStyles.placeholder}
                  secureTextEntry
                />
              </View>
            </View>

            {/* Broker Selection */}
            <View style={styles.inputGroup}>
              <BodyText style={[styles.label, themeStyles.label]}>Platform / Broker *</BodyText>
              <TouchableOpacity
                style={[styles.inputContainer, themeStyles.inputContainer]}
                onPress={() => setIsBrokerModalOpen(true)}
              >
                <Globe size={20} color={themeStyles.icon} style={styles.inputIcon} />
                <BodyText style={[
                  styles.inputText,
                  !selectedBroker && { color: themeStyles.placeholder },
                  selectedBroker && { color: themeStyles.input.color }
                ]}>
                  {selectedBroker ? selectedBroker.name : 'Select Broker'}
                </BodyText>
              </TouchableOpacity>
            </View>

            {/* Server Selection */}
            <View style={styles.inputGroup}>
              <BodyText style={[styles.label, themeStyles.label]}>Server *</BodyText>
              <TouchableOpacity
                style={[
                  styles.inputContainer,
                  themeStyles.inputContainer,
                  !selectedBroker && { opacity: 0.7 }
                ]}
                onPress={() => {
                  if (selectedBroker) setIsServerModalOpen(true);
                  else Alert.alert('Notice', 'Please select a broker first');
                }}
                disabled={!selectedBroker}
              >
                <Server size={20} color={themeStyles.icon} style={styles.inputIcon} />
                <BodyText style={[
                  styles.inputText,
                  !formData.server && { color: themeStyles.placeholder },
                  formData.server && { color: themeStyles.input.color }
                ]}>
                  {formData.server || 'Select Server'}
                </BodyText>
              </TouchableOpacity>
            </View>

            {/* Risk Percentage */}
            <View style={styles.inputGroup}>
              <BodyText style={[styles.label, themeStyles.label]}>Risk Percentage (Max 10%)</BodyText>
              <View style={[styles.inputContainer, themeStyles.inputContainer]}>
                <BodyText style={[styles.percentIcon, { color: themeStyles.icon }]}>%</BodyText>
                <TextInput
                  style={[styles.input, themeStyles.input]}
                  value={formData.riskPercentage}
                  onChangeText={(text) => setFormData({ ...formData, riskPercentage: text })}
                  placeholder="1.00"
                  placeholderTextColor={themeStyles.placeholder}
                  keyboardType="decimal-pad"
                />
              </View>
              <BodyText style={[styles.helperText, { color: colors.placeholder }]}>
                Maximum risk per trade (0% - 10%)
              </BodyText>
            </View>

            {/* Trading Strategy */}
            <View style={styles.inputGroup}>
              <BodyText style={[styles.label, themeStyles.label]}>Trading Strategy</BodyText>
              <View style={styles.strategyContainer}>
                {(['All', 'FVG + Trend', 'Voting'] as const).map((strategy) => (
                  <TouchableOpacity
                    key={strategy}
                    style={[
                      styles.strategyButton,
                      themeStyles.typeButton,
                      formData.strategy === strategy && themeStyles.typeButtonActive,
                    ]}
                    onPress={() => setFormData({ ...formData, strategy })}
                  >
                    <BodyText
                      style={[
                        styles.typeText,
                        themeStyles.typeText,
                        formData.strategy === strategy && themeStyles.typeTextActive,
                      ]}
                    >
                      {strategy}
                    </BodyText>
                    {formData.strategy === strategy && (
                      <CheckCircle
                        size={18}
                        color={colors.primary}
                        style={styles.checkIcon}
                      />
                    )}
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            <Button
              title="Verify & Create Account"
              onPress={handleAddAccount}
              isLoading={isLoading}
              buttonStyle={styles.createButton}
            />
          </View>
        </ScrollView>
      </KeyboardAvoidingView>

      {/* Modals */}
      {renderSelectionModal(isBrokerModalOpen, () => setIsBrokerModalOpen(false), 'Select Broker', true)}
      {renderSelectionModal(isServerModalOpen, () => setIsServerModalOpen(false), 'Select Server', false)}
    </SafeAreaView >
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    padding: Layout.spacing.lg,
    paddingBottom: Layout.spacing.xxl,
  },
  header: {
    marginBottom: Layout.spacing.xl,
  },
  title: {
    fontSize: 24,
  },
  form: {
    gap: Layout.spacing.lg,
  },
  inputGroup: {
    gap: Layout.spacing.xs,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    fontFamily: 'Inter-Medium',
    marginLeft: 4,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderRadius: Layout.borderRadius.md,
    height: 50,
    paddingHorizontal: Layout.spacing.md,
  },
  inputIcon: {
    marginRight: Layout.spacing.sm,
  },
  input: {
    flex: 1,
    fontSize: 16,
    height: '100%',
  },
  percentIcon: {
    fontSize: 18,
    fontWeight: '600',
    marginRight: Layout.spacing.sm,
  },
  helperText: {
    fontSize: 12,
    marginLeft: 4,
    marginTop: 4,
  },
  strategyContainer: {
    gap: Layout.spacing.sm,
  },
  strategyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 48,
    borderRadius: Layout.borderRadius.md,
    borderWidth: 1,
    position: 'relative',
  },
  typeContainer: {
    flexDirection: 'row',
    gap: Layout.spacing.md,
  },
  typeButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 48,
    borderRadius: Layout.borderRadius.md,
    borderWidth: 1,
    position: 'relative',
  },
  typeText: {
    fontSize: 16,
    fontWeight: '500',
    fontFamily: 'Inter-Medium',
  },
  checkIcon: {
    position: 'absolute',
    right: 10,
  },
  createButton: {
    marginTop: Layout.spacing.md,
  },
  inputText: {
    flex: 1,
    fontSize: 16,
    fontFamily: 'Inter-Regular',
  },
  modalOverlay: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  modalContent: {
    height: '70%',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: Layout.spacing.lg,
    borderWidth: 1,
    borderBottomWidth: 0,
    elevation: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Layout.spacing.md,
  },
  modalTitle: {
    fontSize: 20,
  },
  closeButton: {
    fontSize: 16,
    color: '#FF4444',
  },
  listItem: {
    paddingVertical: 15,
    borderBottomWidth: 1,
  },
  listText: {
    fontSize: 16,
  },
});