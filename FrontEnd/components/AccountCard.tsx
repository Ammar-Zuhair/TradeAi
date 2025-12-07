import React from 'react';
import { StyleSheet, TouchableOpacity, View } from 'react-native';
import { SubheadingText, BodyText } from './StyledText';
import { useTheme } from '@/contexts/ThemeContext';
import Layout from '@/constants/Layout';
import { Coins, DollarSign, ExternalLink } from 'lucide-react-native';

export type AccountType = {
  id: string;
  name: string;
  balance: number;
  currency: string;
  profit: number;
  openTrades: number;
  server?: string;
  type: 'Demo' | 'Real' | 'Unknown';
  riskPercentage?: number;
};

type AccountCardProps = {
  account: AccountType;
  onPress: (id: string) => void;
};

export default function AccountCard({ account, onPress }: AccountCardProps) {
  const { colors } = useTheme();
  const isProfit = account.profit >= 0;
  const profitColor = isProfit ? colors.positive : colors.negative;

  // Dynamic styles
  const themeStyles = {
    container: { backgroundColor: colors.card },
    iconContainer: { backgroundColor: colors.surface },
    accountName: { color: colors.text },
    balanceText: { color: colors.text },
    currencyText: { color: colors.placeholder },
    serverText: { color: colors.placeholder },
    tradesContainer: { backgroundColor: colors.surface },
    tradesText: { color: colors.placeholder },
  };

  return (
    <TouchableOpacity
      style={[styles.container, themeStyles.container]}
      onPress={() => onPress(account.id)}
      activeOpacity={0.7}
    >
      <View style={[styles.iconContainer, themeStyles.iconContainer]}>
        <Coins size={28} color={colors.primary} />
      </View>

      <View style={styles.contentContainer}>
        <View style={styles.headerRow}>
          <SubheadingText style={[styles.accountName, themeStyles.accountName]}>{account.name}</SubheadingText>
          <ExternalLink size={18} color={colors.accent} />
        </View>

        <View style={styles.balanceRow}>
          <View style={styles.balanceContainer}>
            <DollarSign size={16} color={colors.text} />
            <SubheadingText style={[styles.balanceText, themeStyles.balanceText]}>
              {account.balance.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </SubheadingText>
            <BodyText style={[styles.currencyText, themeStyles.currencyText]}>{account.currency}</BodyText>
          </View>
          <BodyText style={[styles.profitText, { color: profitColor }]}>
            {isProfit ? '+' : ''}{account.profit.toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </BodyText>
        </View>

        <View style={styles.footer}>
          {account.server && (
            <BodyText style={[styles.serverText, themeStyles.serverText]}>{account.server}</BodyText>
          )}
          <View style={[styles.tradesContainer, themeStyles.tradesContainer]}>
            <BodyText style={[styles.tradesText, themeStyles.tradesText]}>
              {account.openTrades} open trade{account.openTrades !== 1 ? 's' : ''}
            </BodyText>
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: Layout.borderRadius.lg,
    padding: Layout.spacing.md,
    marginBottom: Layout.spacing.md,
    flexDirection: 'row',
  },
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: Layout.borderRadius.md,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: Layout.spacing.md,
  },
  contentContainer: {
    flex: 1,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Layout.spacing.sm,
  },
  accountName: {
    fontSize: 16,
  },
  balanceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Layout.spacing.sm,
  },
  balanceContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  balanceText: {
    fontSize: 18,
    marginLeft: 4,
  },
  currencyText: {
    fontSize: 14,
    marginLeft: 4,
  },
  profitText: {
    fontSize: 14,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  serverText: {
    fontSize: 12,
  },
  tradesContainer: {
    paddingHorizontal: Layout.spacing.sm,
    paddingVertical: Layout.spacing.xs,
    borderRadius: Layout.borderRadius.sm,
  },
  tradesText: {
    fontSize: 12,
  },
});