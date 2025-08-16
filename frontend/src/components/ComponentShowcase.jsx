import React from "react";
import { Button } from "./ui/Button";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/Card";
import { Badge } from "./ui/Badge";

export function ComponentShowcase() {
  return (
    <div className="p-8 space-y-6">
      <Card className="bg-white/10 border-white/20">
        <CardHeader>
          <CardTitle className="text-white">Component Showcase</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-white">Buttons</h4>
            <div className="flex gap-2">
              <Button className="bg-primary-600 hover:bg-primary-700">
                Primary
              </Button>
              <Button
                variant="secondary"
                className="bg-white/20 hover:bg-white/30"
              >
                Secondary
              </Button>
              <Button
                variant="outline"
                className="border-white/30 text-white hover:bg-white/10"
              >
                Outline
              </Button>
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="text-sm font-medium text-white">Badges</h4>
            <div className="flex gap-2">
              <Badge className="bg-green-500">Success</Badge>
              <Badge className="bg-red-500">Error</Badge>
              <Badge className="bg-yellow-500 text-black">Warning</Badge>
              <Badge className="bg-blue-500">Info</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
