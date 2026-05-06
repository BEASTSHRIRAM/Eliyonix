#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { BaseStackProps } from '../lib/types';
import {
  DockerImageStack,
  AgentCoreStack
} from '../lib/stacks';

const app = new cdk.App();
const account =
  process.env.CDK_DEPLOY_ACCOUNT ??
  process.env.CDK_DEFAULT_ACCOUNT ??
  process.env.AWS_ACCOUNT_ID;
const region =
  process.env.CDK_DEPLOY_REGION ??
  process.env.CDK_DEFAULT_REGION ??
  process.env.AWS_REGION ??
  process.env.AWS_DEFAULT_REGION;

const deploymentProps: BaseStackProps = {
  appName: "echoRed",
  // Only pin the stack environment when both values are available.
  env: account && region ? { account, region } : undefined,
  /* If you don't specify 'env', this stack will be environment-agnostic.
   * Account/Region-dependent features and context lookups will not work,
   * but a single synthesized template can be deployed anywhere. */

  /* Uncomment the next line to specialize this stack for the AWS Account
   * and Region that are implied by the current CLI configuration. */
  // env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },

  /* Uncomment the next line if you know exactly what Account and Region you
   * want to deploy the stack to. */
  // env: { account: '123456789012', region: 'us-east-1' },

  /* For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html */
}
const dockerImageStack = new DockerImageStack(app, `echoRed-DockerImageStack`, deploymentProps);
const agentCoreStack = new AgentCoreStack(app, `echoRed-AgentCoreStack`, {
  ...deploymentProps,
  imageUri: dockerImageStack.imageUri
});
agentCoreStack.addDependency(dockerImageStack);
