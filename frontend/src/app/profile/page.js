"use client";

import React from "react";
import { useAuth } from "@/context/AuthContext";
import { 
  User, 
  Mail, 
  Shield, 
  Settings, 
  LogOut, 
  Bell, 
  Key, 
  Activity,
  UserCheck
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

export default function ProfilePage() {
  const { user, signOut } = useAuth();

  if (!user) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <Activity className="w-8 h-8 text-primary animate-spin" />
        <p className="text-muted-foreground font-mono text-sm">Validating session...</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-12 px-6 animate-in fade-in duration-700 space-y-8">
      {/* Profile Header */}
      <div className="flex flex-col md:flex-row items-center gap-8 bg-card/40 backdrop-blur-md p-8 rounded-3xl border border-border/50 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 p-8 opacity-5">
            <User className="w-48 h-48" />
        </div>
        
        <div className="relative">
          <div className="w-32 h-32 rounded-full bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center text-white text-5xl font-black shadow-2xl border-4 border-background">
            {user.email ? user.email.substring(0, 2).toUpperCase() : "US"}
          </div>
          <div className="absolute bottom-1 right-1 w-8 h-8 bg-success rounded-full border-4 border-background flex items-center justify-center shadow-lg">
             <UserCheck className="w-4 h-4 text-white" />
          </div>
        </div>

        <div className="flex-1 text-center md:text-left space-y-2">
          <h1 className="text-3xl font-black text-foreground tracking-tight">
            User Profile
          </h1>
          <div className="flex flex-wrap items-center justify-center md:justify-start gap-4 text-muted-foreground">
            <div className="flex items-center gap-2">
              <Mail className="w-4 h-4 text-primary" />
              <span className="font-medium">{user.email}</span>
            </div>
            <Badge variant="secondary" className="bg-primary/10 text-primary border-primary/20">
              Enterprise Admin
            </Badge>
          </div>
        </div>

        <div className="flex flex-col gap-3 shrink-0">
            <Button variant="outline" onClick={signOut} className="flex items-center gap-2">
                <LogOut className="w-4 h-4" /> Sign Out
            </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Security Summary */}
        <Card className="md:col-span-2 shadow-lg border-border/50 bg-card/60">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Shield className="w-5 h-5 text-primary" /> 
                    Security & Authentication
                </CardTitle>
                <CardDescription>Manage your security credentials and session settings.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
                <div className="flex items-center justify-between p-4 bg-secondary/20 rounded-xl border border-border/30">
                    <div className="flex items-center gap-4">
                        <div className="p-2 bg-primary/10 rounded-lg text-primary">
                            <Key size={18} />
                        </div>
                        <div>
                            <p className="text-sm font-bold">Two-Factor Authentication</p>
                            <p className="text-xs text-muted-foreground">Enabled via Authenticator App</p>
                        </div>
                    </div>
                    <Button variant="outline" size="sm">Configure</Button>
                </div>

                <div className="flex items-center justify-between p-4 bg-secondary/20 rounded-xl border border-border/30">
                    <div className="flex items-center gap-4">
                        <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-500">
                            <Bell size={18} />
                        </div>
                        <div>
                            <p className="text-sm font-bold">Email Notifications</p>
                            <p className="text-xs text-muted-foreground">Critical policy & risk alerts</p>
                        </div>
                    </div>
                    <Button variant="outline" size="sm">Modify</Button>
                </div>
            </CardContent>
        </Card>

        {/* Quick Stats */}
        <Card className="shadow-lg border-border/50 bg-card/60">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Activity className="w-5 h-5 text-primary" /> 
                    Platform Activity
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="space-y-1">
                    <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Last Login</p>
                    <p className="text-sm font-medium">March 27, 2026 • 09:42 AM</p>
                </div>
                <div className="space-y-1">
                    <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Analyses Run</p>
                    <p className="text-sm font-medium">14 Total</p>
                </div>
                <div className="space-y-1">
                    <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Portfolio Access</p>
                    <p className="text-sm font-medium">Read/Write/Execute</p>
                </div>
                <div className="pt-4 mt-4 border-t border-border/30">
                    <Button className="w-full gap-2" variant="outline">
                        <Settings className="w-4 h-4" /> Account Settings
                    </Button>
                </div>
            </CardContent>
        </Card>
      </div>
    </div>
  );
}
