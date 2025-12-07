import React, { useState, useEffect } from 'react';

import {
  View,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  Dimensions,
  TextInput,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { LineChart } from 'react-native-chart-kit';
import { Bell, Search, X } from 'lucide-react-native';
import Animated, { FadeIn, FadeInDown, useAnimatedStyle, withTiming, useSharedValue } from 'react-native-reanimated';

import { useAuth } from '@/contexts/AuthContext';
import { useAccounts } from '@/contexts/AccountsContext';
import { useTheme } from '@/contexts/ThemeContext';
import Layout from '@/constants/Layout';
import { HeadingText, BodyText } from '@/components/StyledText';
import AccountCard from '@/components/AccountCard';

export default function DashboardScreen() {
  const { user } = useAuth();
  const { accounts, isLoading, activeAccountId } = useAccounts();
  const { colors } = useTheme();
  const [refreshing, setRefreshing] = useState(false);
  const [totalBalance, setTotalBalance] = useState(0);
  const [totalProfit, setTotalProfit] = useState(0);

  // Search state
  const [isSearching, setIsSearching] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const searchWidth = useSharedValue(0);

  // Calculation for total balance and profit
  useEffect(() => {
    let balance = 0;
    let profit = 0;

    accounts.forEach(account => {
      // If activeAccountId is set, only include that account
      if (activeAccountId && account.id !== activeAccountId) return;

      balance += account.balance;
      profit += account.profit;
    });

    setTotalBalance(balance);
    setTotalProfit(profit);
  }, [accounts, activeAccountId]);

  const onRefresh = async () => {
    setRefreshing(true);

    // Simulate API refresh
    await new Promise(resolve => setTimeout(resolve, 1500));

    setRefreshing(false);
  };

  const handleAccountPress = (id: string) => {
    router.push({
      pathname: '/account/[id]',
      params: { id }
    });
  };

  const toggleSearch = () => {
    if (isSearching) {
      // Close search
      setSearchQuery('');
      searchWidth.value = withTiming(0);
      setTimeout(() => setIsSearching(false), 300);
    } else {
      // Open search
      setIsSearching(true);
      searchWidth.value = withTiming(1);
    }
  };

  const searchAnimatedStyle = useAnimatedStyle(() => {
    return {
      flex: searchWidth.value,
      opacity: searchWidth.value,
    };
  });

  // Filter accounts based on search query
  const filteredAccounts = accounts.filter(account =>
    account.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Mock data for chart
  const chartData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [
      {
        data: [
          Math.random() * 10000,
          Math.random() * 10000,
          Math.random() * 10000,
          Math.random() * 10000,
          Math.random() * 10000,
          totalBalance,
        ],
        color: (opacity = 1) => `rgba(91, 72, 210, ${opacity})`,
        strokeWidth: 2
      }
    ],
  };

  // Dynamic styles
  const themeStyles = {
    container: { backgroundColor: colors.surface },
    headerText: { color: colors.text },
    subText: { color: colors.placeholder },
    card: { backgroundColor: colors.card },
    iconButton: { backgroundColor: colors.card },
    sectionTitle: { color: colors.text },
    noAccountsText: { color: colors.placeholder },
    searchInput: {
      color: colors.text,
      backgroundColor: colors.card,
    },
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
          {!isSearching ? (
            <View style={styles.headerTextContainer}>
              <Animated.Text
                style={[styles.greeting, themeStyles.headerText]}
                entering={FadeIn.delay(200)}
              >
                Hello, {user?.name || 'Trader'}
              </Animated.Text>
              <Animated.Text
                style={[styles.date, themeStyles.subText]}
                entering={FadeIn.delay(300)}
              >
                {new Date().toLocaleDateString('en-US', {
                  weekday: 'long',
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })}
              </Animated.Text>
            </View>
          ) : (
            <Animated.View style={[styles.searchContainer, searchAnimatedStyle]}>
              <TextInput
                style={[styles.searchInput, themeStyles.searchInput]}
                placeholder="Search accounts..."
                placeholderTextColor={colors.placeholder}
                value={searchQuery}
                onChangeText={setSearchQuery}
                autoFocus
              />
            </Animated.View>
          )}

          <View style={styles.headerIcons}>
            <TouchableOpacity
              style={[styles.iconButton, themeStyles.iconButton]}
              onPress={toggleSearch}
            >
              {isSearching ? (
                <X size={24} color={colors.text} />
              ) : (
                <Search size={24} color={colors.text} />
              )}
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.iconButton, themeStyles.iconButton]}
              onPress={() => router.push('/notifications')}
            >
              <Bell size={24} color={colors.text} />
            </TouchableOpacity>
          </View>
        </View>

        <Animated.View
          style={[styles.balanceContainer, themeStyles.card]}
          entering={FadeInDown.delay(400).springify()}
        >
          <BodyText style={[styles.balanceLabel, themeStyles.subText]}>Total Balance</BodyText>
          <HeadingText style={[styles.balanceAmount, themeStyles.headerText]}>
            ${totalBalance.toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </HeadingText>
          <View style={styles.profitContainer}>
            <BodyText style={[
              styles.profitAmount,
              { color: totalProfit >= 0 ? colors.positive : colors.negative }
            ]}>
              {totalProfit >= 0 ? '+' : ''}{totalProfit.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </BodyText>
            <BodyText style={[styles.todayText, themeStyles.subText]}>today</BodyText>
          </View>
        </Animated.View>

        <Animated.View
          style={styles.chartContainer}
          entering={FadeInDown.delay(500).springify()}
        >
          <LineChart
            data={chartData}
            width={Dimensions.get('window').width - 32}
            height={220}
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

        <View style={styles.accountsSection}>
          <HeadingText style={[styles.sectionTitle, themeStyles.sectionTitle]}>
            {isSearching ? 'Search Results' : 'Your Accounts'}
          </HeadingText>

          {filteredAccounts.length === 0 ? (
            <Animated.View
              style={[styles.noAccountsContainer, themeStyles.card]}
              entering={FadeInDown.delay(600)}
            >
              <BodyText style={[styles.noAccountsText, themeStyles.noAccountsText]}>
                {isSearching
                  ? `No accounts found matching "${searchQuery}"`
                  : "You don't have any trading accounts yet."}
              </BodyText>
            </Animated.View>
          ) : (
            filteredAccounts.map((account, index) => (
              <Animated.View
                key={account.id}
                entering={FadeInDown.delay(600 + (index * 100)).springify()}
              >
                <AccountCard
                  account={account}
                  onPress={handleAccountPress}
                />
              </Animated.View>
            ))
          )}
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
    alignItems: 'center', // Changed from flex-start to center for better alignment with search
    marginBottom: Layout.spacing.lg,
    height: 50, // Fixed height to prevent jumping when switching to search
  },
  headerTextContainer: {
    flex: 1,
  },
  greeting: {
    fontSize: 24,
    fontWeight: '700',
    fontFamily: 'Inter-Bold',
    marginBottom: 4,
  },
  date: {
    fontSize: 14,
    fontFamily: 'Inter-Regular',
  },
  searchContainer: {
    flex: 1,
    marginRight: Layout.spacing.sm,
  },
  searchInput: {
    height: 40,
    borderRadius: Layout.borderRadius.md,
    paddingHorizontal: Layout.spacing.md,
    fontSize: 16,
  },
  headerIcons: {
    flexDirection: 'row',
  },
  iconButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: Layout.spacing.sm,
  },
  balanceContainer: {
    borderRadius: Layout.borderRadius.lg,
    padding: Layout.spacing.lg,
    marginBottom: Layout.spacing.lg,
  },
  balanceLabel: {
    fontSize: 14,
    marginBottom: 4,
  },
  balanceAmount: {
    fontSize: 32,
    marginBottom: 8,
  },
  profitContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  profitAmount: {
    fontSize: 16,
    fontWeight: '600',
    fontFamily: 'Inter-Medium',
  },
  todayText: {
    fontSize: 14,
    marginLeft: 6,
  },
  chartContainer: {
    marginBottom: Layout.spacing.lg,
  },
  chart: {
    borderRadius: Layout.borderRadius.lg,
  },
  accountsSection: {
    marginBottom: Layout.spacing.xl,
  },
  sectionTitle: {
    fontSize: 20,
    marginBottom: Layout.spacing.md,
  },
  noAccountsContainer: {
    borderRadius: Layout.borderRadius.lg,
    padding: Layout.spacing.lg,
    alignItems: 'center',
    justifyContent: 'center',
    height: 150,
  },
  noAccountsText: {
    textAlign: 'center',
  },
});