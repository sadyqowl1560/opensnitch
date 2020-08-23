package views

import (
	"fmt"
	"time"

	"github.com/gustavo-iniguez-goya/opensnitch/daemon/log"
	"github.com/gustavo-iniguez-goya/opensnitch/daemon/ui/protocol"
	"github.com/gustavo-iniguez-goya/opensnitch/server/api"
)

var (
	actionDeny  = log.Bold(log.Red(api.ActionDeny))
	actionAllow = log.Bold(log.Green(api.ActionAllow))
	eventAction = actionDeny
	printFormat = printFormatPretty
	eventTime   = ""
)

// PrintStatus prints an overview of the node statistics.
func PrintStatus() {
	waitForStats()

	stats := config.apiClient.GetLastStats()
	uptime, _ := time.ParseDuration(fmt.Sprint(stats.Uptime, "s"))

	appTitle := fmt.Sprint(UNDERLINE, appName+" - "+stats.DaemonVersion+log.RESET)

	fmt.Printf("\n\t%s\n\n"+
		"\tRules:\t\t%d\n"+
		"\tUptime:\t\t%s\n"+
		"\tDnsResponses:\t%d\n"+
		"\tConnections:\t%d\n"+
		"\tIgnored:\t%d\n"+
		"\tAccepted:\t%d\n"+
		"\tDropped:\t%d\n"+
		"\tRules hits:\t%d\n"+
		"\tRules missed:\t%d\n\n",
		log.Bold(appTitle),
		stats.Rules,
		uptime,
		stats.DnsResponses,
		stats.Connections,
		stats.Ignored,
		stats.Accepted,
		stats.Dropped,
		stats.RuleHits,
		stats.RuleMisses,
	)
}

func printHelp() {
	cleanLine()
	fmt.Printf("\n\tr/c - continue viewing statistics\n")
	fmt.Printf("\tp   - pause statistics\n")
	fmt.Printf("\tq   - stop and exit\n")
	fmt.Printf("\t><  - view next/preview statistics\n")
	//fmt.Printf("\tl   - limit statistics\n")
	//fmt.Printf("\tf   - filter statistics\n")
	fmt.Printf("\th   - help\n")
	fmt.Printf("\n")
	cleanLine()
}

func printConnectionDetails() {
	// TODO
}

// print statistics by type (procs, hosts, ports, addrs...)
func printStats(what string, hits uint64) {
	fmt.Printf("  %-5d - %v%*s\n", hits, what, ttyCols-len(what)-10, ".")
}

// print details of an event
func printEvent(e *protocol.Event) {
	eventAction = actionDeny
	eventTime = log.Wrap(fmt.Sprintf("%v", e.Time), CYAN)
	if e.Rule.Action == api.ActionAllow {
		eventAction = actionAllow
	}

	printFormat = printFormatPretty
	if config.Style == ViewStylePlain {
		printFormat = printFormatPlain
		eventAction = e.Rule.Action
	}

	fmt.Printf(printFormat,
		eventTime,
		config.Delimiter,
		eventAction,
		config.Delimiter,
		e.Connection.Protocol,
		config.Delimiter,
		e.Connection.UserId,
		config.Delimiter,
		e.Connection.SrcPort,
		config.Delimiter,
		e.Connection.SrcIp,
		config.Delimiter,
		e.Connection.DstIp,
		config.Delimiter,
		e.Connection.DstPort,
		config.Delimiter,
		e.Connection.ProcessPath,
		log.RESET)
}