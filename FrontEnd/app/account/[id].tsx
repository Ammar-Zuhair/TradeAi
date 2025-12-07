import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, router } from 'expo-router';
import { ArrowLeft, Trash2, ChartBar as BarChart2, DollarSign, FileSliders as Sliders } from 'lucide-react-native';
import { LineChart } from 'react-native-chart-kit';
import Animated, { FadeInDown } from 'react-native-reanimated';

import { useAccounts } from '@/contexts/AccountsContext';
import { useTheme } from '@/contexts/ThemeContext';
import Layout from '@/constants/Layout';
import { HeadingText, BodyText } from '@/components/StyledText';
import TradeCard from '@/components/TradeCard';
import Button from '@/components/Button';

export default function AccountDetailsScreen() {
  const { id } = useLocalSearchParams();
  const { accounts, getAccountTrades, removeAccount } = useAccounts();
  const { colors } = useTheme();
  const [refreshing, setRefreshing] = useState(false);

  // Find the account with the given ID
  const account = accounts.find(acc => acc.id === id);
  // Get trades for this account
  const trades = getAccountTrades(id as string);

  // If account not found, go back to dashboard
  useEffect(() => {
    if (!account) {
      router.replace('/(tabs)');
    }
  }, [account]);

  const onRefresh = async () => {
    setRefreshing(true);

    // Simulate API refresh
    await new Promise(resolve => setTimeout(resolve, 1500));

    setRefreshing(false);
  };

  const handleRemoveAccount = () => {
    Alert.alert(
      'Remove Account',
      'Are you sure you want to remove this account? This action cannot be undone.',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Remove',
          onPress: async () => {
            await removeAccount(id as string);
            router.replace('/(tabs)');
          },
          style: 'destructive',
        },
      ]
    );
  };

  const handleTradePress = (tradeId: string) => {
    // Navigate to trade details or implement action
    console.log('Trade pressed:', tradeId);
  };

  // Mock data for the balance chart
  const balanceData = {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Today'],
    datasets: [
      {
        data: [
          account?.balance ? account.balance * 0.95 : 1000,
          account?.balance ? account.balance * 0.97 : 1200,
          account?.balance ? account.balance * 0.96 : 1100,
          account?.balance ? account.balance * 0.98 : 1300,
          account?.balance ? account.balance * 0.99 : 1400,
          account?.balance || 1500,
        ],
        color: (opacity = 1) => `rgba(91, 72, 210, ${opacity})`,
        strokeWidth: 2
      }
    ],
  };

  if (!account) {
    return null; // This will be handled by the useEffect
  }

  // Dynamic styles
  const themeStyles = {
    container: { backgroundColor: colors.surface },
    title: { color: colors.text },
    balanceCard: { backgroundColor: colors.card },
    balanceLabel: { color: colors.placeholder },
    balanceAmount: { color: colors.text },
    currencyText: { color: colors.placeholder },
    profitLabel: { color: colors.placeholder },
    statCard: { backgroundColor: colors.card },
    statIconContainer: { backgroundColor: 'rgba(91, 72, 210, 0.15)' },
    statLabel: { color: colors.placeholder },
    statValue: { color: colors.text },
    statValueSmall: { color: colors.text },
    sectionTitle: { color: colors.text },
    noTradesContainer: { backgroundColor: colors.card },
    noTradesText: { color: colors.placeholder },
  };

  return (
    <SafeAreaView style={[styles.container, themeStyles.container]} edges={['top']}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={colors.primary}
            colors={[colors.primary]}
          />
        }
      >
        <View style={styles.header}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => router.back()}
          >
            <ArrowLeft size={24} color={colors.text} />
          </TouchableOpacity>
          <HeadingText style={[styles.title, themeStyles.title]}>{account.name}</HeadingText>
          <TouchableOpacity
            style={styles.deleteButton}
            onPress={handleRemoveAccount}
          >
            <Trash2 size={20} color={colors.negative} />
          </TouchableOpacity>
        </View>

        <Animated.View
          style={[styles.balanceCard, themeStyles.balanceCard]}
          entering={FadeInDown.delay(200).springify()}
        >
          <View style={styles.balanceHeader}>
            <View>
              <BodyText style={[styles.balanceLabel, themeStyles.balanceLabel]}>Current Balance</BodyText>
              <View style={styles.balanceRow}>
                <DollarSign size={24} color={colors.text} />
                <HeadingText style={[styles.balanceAmount, themeStyles.balanceAmount]}>
                  {account.balance.toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </HeadingText>
                <BodyText style={[styles.currencyText, themeStyles.currencyText]}>{account.currency}</BodyText>
              </View>
            </View>

            <View style={styles.profitContainer}>
              <BodyText style={[styles.profitLabel, themeStyles.profitLabel]}>Today's P/L</BodyText>
              <BodyText style={[
                styles.profitAmount,
                { color: account.profit >= 0 ? colors.positive : colors.negative }
              ]}>
                {account.profit >= 0 ? '+' : ''}{account.profit.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </BodyText>
            </View>
          </View>

          <LineChart
            data={balanceData}
            width={Layout.window.width - 48}
            height={180}
            yAxisLabel="$"
            yAxisSuffix=""
            chartConfig={{
              backgroundColor: colors.card,
              backgroundGradientFrom: colors.card,
              backgroundGradientTo: colors.card,
              decimalPlaces: 0,
              color: (opacity = 1) => colors.text === '#000' ? `rgba(0, 0, 0, ${opacity})` : `rgba(255, 255, 255, ${opacity})`,
              labelColor: (opacity = 1) => colors.text === '#000' ? `rgba(0, 0, 0, ${opacity})` : `rgba(255, 255, 255, ${opacity})`,
              style: {
                borderRadius: 16,
              },
              propsForDots: {
                r: '6',
                strokeWidth: '2',
                stroke: colors.primary,
              },
            }}
            bezier
            style={styles.chart}
          />
        </Animated.View>

        <View style={styles.statsContainer}>
          <Animated.View
            style={[styles.statCard, themeStyles.statCard]}
            entering={FadeInDown.delay(300).springify()}
          >
            <View style={[styles.statIconContainer, themeStyles.statIconContainer]}>
              <BarChart2 size={20} color={colors.primary} />
            </View>
            <BodyText style={[styles.statLabel, themeStyles.statLabel]}>Open Trades</BodyText>
            <HeadingText style={[styles.statValue, themeStyles.statValue]}>{account.openTrades}</HeadingText>
          </Animated.View>

          <Animated.View
            style={[styles.statCard, themeStyles.statCard]}
            entering={FadeInDown.delay(400).springify()}
          >
            <View style={[styles.statIconContainer, themeStyles.statIconContainer]}>
              <Sliders size={20} color={colors.primary} />
            </View>
            <BodyText style={[styles.statLabel, themeStyles.statLabel]}>Server</BodyText>
            <BodyText style={[styles.statValueSmall, themeStyles.statValueSmall]}>{account.server || 'Not specified'}</BodyText>
          </Animated.View>
        </View>

        <View style={styles.tradesSection}>
          <HeadingText style={[styles.sectionTitle, themeStyles.sectionTitle]}>Open Trades</HeadingText>

          {trades.length === 0 ? (
            <View style={[styles.noTradesContainer, themeStyles.noTradesContainer]}>
              <BodyText style={[styles.noTradesText, themeStyles.noTradesText]}>
                No open trades found for this account.
              </BodyText>
            </View>
          ) : (
            trades.map((trade, index) => (
              <Animated.View
                key={trade.id}
                entering={FadeInDown.delay(500 + (index * 100)).springify()}
              >
                <TradeCard trade={trade} onPress={handleTradePress} />
              </Animated.View>
            ))
          )}
        </View>

        <View style={styles.actionsContainer}>
          <Button
            title="Close All Trades"
            variant="danger"
            disabled={trades.length === 0}
            buttonStyle={styles.actionButton}
          />

          <Button
            title="Trade History"
            variant="secondary"
            buttonStyle={styles.actionButton}
            onPress={() => router.push('/(tabs)/history')}
          />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    padding: Layout.spacing.md,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Layout.spacing.lg,
  },
  backButton: {
    padding: Layout.spacing.xs,
  },
  title: {
    fontSize: 20,
  },
  deleteButton: {
    padding: Layout.spacing.xs,
  },
  balanceCard: {
    borderRadius: Layout.borderRadius.lg,
    padding: Layout.spacing.lg,
    marginBottom: Layout.spacing.lg,
  },
  balanceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: Layout.spacing.md,
  },
  balanceLabel: {
    fontSize: 14,
    marginBottom: 4,
  },
  balanceRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  balanceAmount: {
    fontSize: 28,
    marginLeft: 4,
  },
  currencyText: {
    fontSize: 14,
    alignSelf: 'flex-end',
    marginLeft: 4,
    marginBottom: 4,
  },
  profitContainer: {
    alignItems: 'flex-end',
  },
  profitLabel: {
    fontSize: 14,
    marginBottom: 4,
  },
  profitAmount: {
    fontSize: 18,
    fontWeight: '600',
    fontFamily: 'Inter-Medium',
  },
  chart: {
    marginTop: Layout.spacing.sm,
    borderRadius: Layout.borderRadius.lg,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: Layout.spacing.lg,
  },
  statCard: {
    flex: 1,
    borderRadius: Layout.borderRadius.lg,
    padding: Layout.spacing.lg,
    marginHorizontal: 4,
    alignItems: 'center',
  },
  statIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: Layout.spacing.sm,
  },
  statLabel: {
    fontSize: 14,
    marginBottom: 4,
  },
  statValue: {
    fontSize: 24,
    fontWeight: '600',
    fontFamily: 'Inter-Medium',
  },
  statValueSmall: {
    fontSize: 14,
    textAlign: 'center',
  },
  tradesSection: {
    marginBottom: Layout.spacing.lg,
  },
  sectionTitle: {
    fontSize: 18,
    marginBottom: Layout.spacing.md,
  },
  noTradesContainer: {
    borderRadius: Layout.borderRadius.lg,
    padding: Layout.spacing.lg,
    alignItems: 'center',
    justifyContent: 'center',
    height: 150,
  },
  noTradesText: {
    textAlign: 'center',
  },
  actionsContainer: {
    marginBottom: Layout.spacing.xxl,
  },
  actionButton: {
    marginBottom: Layout.spacing.md,
  },
});